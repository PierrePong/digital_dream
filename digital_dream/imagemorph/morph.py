import numpy as np
import tensorflow as tf
import tensorflow_addons as tfa
import cv2
from datetime import datetime as dt
from imagemorph.utils import BUCKET_NAME, save_to_gcp, get_image_from_bucket
import os

TRAIN_EPOCHS = 1000

im_sz = 512
mp_sz = 96

warp_scale = 1
mult_scale = 0.4
add_scale = 0.4
add_first = False

timestamp = str(dt.date(dt.now()))


@tf.function 
def warp(origins, targets, preds_org, preds_trg):
    if add_first:
        res_targets = tfa.image.dense_image_warp((origins + preds_org[:,:,:,3:6] * 2 * add_scale) * tf.maximum(0.1, 1 + preds_org[:,:,:,0:3] * mult_scale) , preds_org[:,:,:,6:8] * im_sz * warp_scale )        
        res_origins = tfa.image.dense_image_warp((targets + preds_trg[:,:,:,3:6] * 2 * add_scale) * tf.maximum(0.1, 1 + preds_trg[:,:,:,0:3] * mult_scale) , preds_trg[:,:,:,6:8] * im_sz * warp_scale )
    else:
        res_targets = tfa.image.dense_image_warp(origins * tf.maximum(0.1, 1 + preds_org[:,:,:,0:3] * mult_scale) + preds_org[:,:,:,3:6] * 2 * add_scale, preds_org[:,:,:,6:8] * im_sz * warp_scale )        
        res_origins = tfa.image.dense_image_warp(targets * tf.maximum(0.1, 1 + preds_trg[:,:,:,0:3] * mult_scale) + preds_trg[:,:,:,3:6] * 2 * add_scale, preds_trg[:,:,:,6:8] * im_sz * warp_scale )

    return res_targets, res_origins

def create_grid(scale):
    grid = np.mgrid[0:scale,0:scale] / (scale - 1) * 2 -1
    grid = np.swapaxes(grid, 0, 2)
    grid = np.expand_dims(grid, axis=0)
    return grid


def produce_warp_maps(origins, targets, img_):
    class MyModel(tf.keras.Model):
        def __init__(self):
            super(MyModel, self).__init__()
            self.conv1 = tf.keras.layers.Conv2D(64, (5, 5))
            self.act1 = tf.keras.layers.LeakyReLU(alpha=0.2)
            self.conv2 = tf.keras.layers.Conv2D(64, (5, 5))
            self.act2 = tf.keras.layers.LeakyReLU(alpha=0.2)
            self.convo = tf.keras.layers.Conv2D((3 + 3 + 2) * 2, (5, 5))

        def call(self, maps):
            x = tf.image.resize(maps, [mp_sz, mp_sz])
            x = self.conv1(x)
            x = self.act1(x)
            x = self.conv2(x)
            x = self.act2(x)
            x = self.convo(x)
            return x


    model = MyModel()

    loss_object = tf.keras.losses.MeanSquaredError()
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.0002)

    train_loss = tf.keras.metrics.Mean(name='train_loss')

    @tf.function
    def train_step(maps, origins, targets, img_):
      with tf.GradientTape() as tape:
        preds = model(maps)
        preds = tf.image.resize(preds, [im_sz, im_sz])
        
        #a = tf.random.uniform([maps.shape[0]])
        #res_targets, res_origins = warp(origins, targets, preds[...,:8] * a, preds[...,8:] * (1 - a))
        res_targets_, res_origins_ = warp(origins, targets, preds[...,:8], preds[...,8:])
        
        res_map = tfa.image.dense_image_warp(maps, preds[:,:,:,6:8] * im_sz * warp_scale ) #warp maps consistency checker   
        res_map = tfa.image.dense_image_warp(res_map, preds[:,:,:,14:16] * im_sz * warp_scale ) 
        
        loss = loss_object(maps, res_map) * 1 + loss_object(res_targets_, targets) * 0.3 + loss_object(res_origins_, origins) * 0.3
        
      gradients = tape.gradient(loss, model.trainable_variables)
      optimizer.apply_gradients(zip(gradients, model.trainable_variables))

      train_loss(loss)
      
    maps = create_grid(im_sz)
    maps = np.concatenate((maps, origins * 0.1, targets * 0.1), axis=-1).astype(np.float32)
  
    
    template = 'Epoch {}, Loss: {}'
    for i in range(TRAIN_EPOCHS):
        epoch = i + 1  
        train_step(maps, origins, targets, img_=img_)

        if epoch % 10 == 0:
            print (template.format(epoch, train_loss.result()))  

        
        # if (epoch < 100 and epoch % 10 == 0) or\
        #    (epoch < 1000 and epoch % 100 == 0) or\
        #    (epoch % 1000 == 0):
            preds = model(maps, training=False)[:1]
            preds = tf.image.resize(preds, [im_sz, im_sz])
            
            res_targets, res_origins = warp(origins, targets, preds[...,:8], preds[...,8:])
            
            res_targets = tf.clip_by_value(res_targets, -1, 1)[0]
            res_img = ((res_targets.numpy() + 1) * 127.5).astype(np.uint8)
            cv2.imwrite(f"data/train/a_to_b_%d.jpg" % epoch, cv2.cvtColor(res_img, cv2.COLOR_RGB2BGR))
            save_to_gcp(f"dreams/trains/train_{timestamp}/train{img_}/a_to_b_{epoch}.jpg", f"data/train/a_to_b_{epoch}.jpg", rm_local=False)
            
            res_origins = tf.clip_by_value(res_origins, -1, 1)[0]
            res_img = ((res_origins.numpy() + 1) * 127.5).astype(np.uint8)
            cv2.imwrite(f"data/train/b_to_a_%d.jpg" % epoch, cv2.cvtColor(res_img, cv2.COLOR_RGB2BGR))
            save_to_gcp(f"dreams/trains/train_{timestamp}/train{img_}/b_to_a_{epoch}.jpg", f"data/train/b_to_a_{epoch}.jpg", rm_local=False)

            np.save('preds.npy', preds.numpy())
        
def use_warp_maps(origins, targets, img_):
    STEPS = 201
  
    preds = np.load('preds.npy')
    
    #save maps as images
    res_img = np.zeros((im_sz * 2, im_sz * 3, 3))

    res_img[im_sz*0:im_sz*1, im_sz*0:im_sz*1] = preds[0,:,:,0:3] # a_to_b add map
    res_img[im_sz*0:im_sz*1, im_sz*1:im_sz*2] = preds[0,:,:,3:6] # a_to_b mult map
    res_img[im_sz*0:im_sz*1, im_sz*2:im_sz*3, :2] = preds[0,:,:,6:8] # a_to_b warp map
    
    res_img[im_sz*1:im_sz*2, im_sz*0:im_sz*1] = preds[0,:,:,8:11] # b_to_a add map
    res_img[im_sz*1:im_sz*2, im_sz*1:im_sz*2] = preds[0,:,:,11:14] # b_to_a mult map
    res_img[im_sz*1:im_sz*2, im_sz*2:im_sz*3, :2] = preds[0,:,:,14:16] # b_to_a warp map
    
    res_img = np.clip(res_img, -1, 1)
    res_img = ((res_img + 1) * 127.5).astype(np.uint8)
    cv2.imwrite("data/morph/maps.jpg", cv2.cvtColor(res_img, cv2.COLOR_RGB2BGR))
    save_to_gcp(f"dreams/morphs/maps-{timestamp}/maps{img_}.jpg", "data/morph/maps.jpg", rm_local=False)

    
    #apply maps and save results
    
    org_strength = tf.reshape(tf.range(STEPS, dtype=tf.float32), [STEPS, 1, 1, 1]) / (STEPS - 1) 
    trg_strength = tf.reverse(org_strength, axis = [0])
 
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(f'data/morph/morph.mp4', fourcc, 48, (im_sz, im_sz))
    img_a = np.zeros((im_sz, im_sz * (STEPS // 10), 3), dtype = np.uint8)
    img_b = np.zeros((im_sz, im_sz * (STEPS // 10), 3), dtype = np.uint8)
    img_a_b = np.zeros((im_sz, im_sz * (STEPS // 10), 3), dtype = np.uint8)
    
    res_img = np.zeros((im_sz * 3, im_sz * (STEPS // 10), 3), dtype = np.uint8)
    
    for i in range(STEPS):
        preds_org = preds * org_strength[i]
        preds_trg = preds * trg_strength[i]
    
        res_targets, res_origins = warp(origins, targets, preds_org[...,:8], preds_trg[...,8:])
        res_targets = tf.clip_by_value(res_targets, -1, 1)
        res_origins = tf.clip_by_value(res_origins, -1, 1)
        
        results = res_targets * trg_strength + res_origins * org_strength
        res_numpy = results.numpy()
    
        img = ((res_numpy[i] + 1) * 127.5).astype(np.uint8)
        video.write(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

        if (i+1) % 10 == 0:
            res_img[im_sz*0:im_sz*1, i // 10 * im_sz : (i // 10 + 1) * im_sz] = img
            res_img[im_sz*1:im_sz*2, i // 10 * im_sz : (i // 10 + 1) * im_sz] = ((res_targets.numpy()[0] + 1) * 127.5).astype(np.uint8)
            res_img[im_sz*2:im_sz*3, i // 10 * im_sz : (i // 10 + 1) * im_sz] = ((res_origins.numpy()[0] + 1) * 127.5).astype(np.uint8)
            print ('Image #%d produced.' % (i + 1))
            
    cv2.imwrite("data/morph/result.jpg", cv2.cvtColor(res_img, cv2.COLOR_RGB2BGR))
    save_to_gcp(f"dreams/morphs/maps-{timestamp}/result{img_}", local_path="data/morph/result.jpg", rm_local=False)
    
    cv2.destroyAllWindows()
    video.release()   
    save_to_gcp(f"dreams/morphs/videos-{timestamp}/video{img_}.mp4", "data/morph/morph.mp4", rm_local=False)

    print ('Result video saved.')
    
    
if __name__ == "__main__":

    path = "Clusters/cluster_2021-06-15_16-16_0"
    local_path = "images"

    for img_ in range(4,19):
        source_path = "{}/{}.jpg".format(path, img_)
        target_path = "{}/{}.jpg".format(path, img_+1)
        # source_path = df.loc[i, 0]
        # target_path = df.loc[i + 1, 0]


        source = get_image_from_bucket(source_path, local_path)
        target = get_image_from_bucket(target_path,local_path)

    # dom_a = cv2.imread(args.source, cv2.IMREAD_COLOR)

        dom_a = get_image_from_bucket(source_path, local_path)
        # dom_a = cv2.imread(source, cv2.IMREAD_COLOR)
        dom_a = cv2.cvtColor(dom_a, cv2.COLOR_BGR2RGB)
        dom_a = cv2.resize(dom_a, (im_sz, im_sz), interpolation = cv2.INTER_AREA)
        dom_a = dom_a / 127.5 - 1

        # dom_b = cv2.imread(args.target, cv2.IMREAD_COLOR)
        dom_b = get_image_from_bucket(target_path,local_path)
        # dom_b = cv2.imread(target, cv2.IMREAD_COLOR)
        dom_b = cv2.cvtColor(dom_b, cv2.COLOR_BGR2RGB)
        dom_b = cv2.resize(dom_b, (im_sz, im_sz), interpolation = cv2.INTER_AREA)
        dom_b = dom_b / 127.5 - 1

        origins = dom_a.reshape(1, im_sz, im_sz, 3).astype(np.float32)
        targets = dom_b.reshape(1, im_sz, im_sz, 3).astype(np.float32)

        produce_warp_maps(origins, targets, img_=img_)
        use_warp_maps(origins, targets, img_=img_)
        
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        path = "raw_data"
        final_clip = VideoFileClip(f"{path}/video0.mp4")
        for i in range(1,4):
            clip = VideoFileClip(f"{path}/video{i}.mp4") #
            final_clip = concatenate_videoclips([final_clip,clip])
        final_clip.write_videofile(f"{path}/Dreams.mp4")
        
        
        
        for folder in ['data/morph', 'data/train']:
            for file in os.listdir(folder):
                os.remove(os.path.join(folder, file))