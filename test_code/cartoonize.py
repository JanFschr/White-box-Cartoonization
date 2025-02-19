import os
import cv2
import numpy as np
import tensorflow as tf 
import network
import guided_filter
import argparse

from tqdm import tqdm

import warnings
warnings.filterwarnings('ignore',category=FutureWarning)

tf.compat.v1.disable_eager_execution()

def arg_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument("--saved_model_path", default = 'saved_models', type = str)
    parser.add_argument("--load_folder", default = 'test_images', type = str)
    parser.add_argument("--save_folder", default = 'cartoonized_images', type = str)
    #parser.add_argument("--fast_shrink", default = True, type = boolean)

    


    args = parser.parse_args()
    
    return args


def resize_crop(image):
    h, w, c = np.shape(image)
    if min(h, w) > 720:
        if h > w:
            h, w = int(720*h/w), 720
        else:
            h, w = 720, int(720*w/h)
    image = cv2.resize(image, (w, h),
                       interpolation=cv2.INTER_AREA)
    h, w = (h//8)*8, (w//8)*8
    image = image[:h, :w, :]
    return image
    

def cartoonize(load_folder, save_folder, model_path):
    input_photo = tf.compat.v1.placeholder(tf.float32, [1, None, None, 3])
    network_out = network.unet_generator(input_photo)
    final_out = guided_filter.guided_filter(input_photo, network_out, r=1, eps=5e-3)

    all_vars = tf.compat.v1.trainable_variables()
    gene_vars = [var for var in all_vars if 'generator' in var.name]
    saver = tf.compat.v1.train.Saver(var_list=gene_vars)
    
    config = tf.compat.v1.ConfigProto()
    config.gpu_options.allow_growth = True
    sess = tf.compat.v1.Session(config=config)

    sess.run(tf.compat.v1.global_variables_initializer())
    saver.restore(sess, tf.train.latest_checkpoint(model_path))
    name_list = os.listdir(load_folder)
    for name in tqdm(name_list):
        try:
            load_path = os.path.join(load_folder, name)
            save_path = os.path.join(save_folder, name)
            image = cv2.imread(load_path)
            image = resize_crop(image)
            batch_image = image.astype(np.float32)/127.5 - 1
            batch_image = np.expand_dims(batch_image, axis=0)
            output = sess.run(final_out, feed_dict={input_photo: batch_image})
            output = (np.squeeze(output)+1)*127.5
            output = np.clip(output, 0, 255).astype(np.uint8)
            cv2.imwrite(save_path, output)
        except:
            print('cartoonize {} failed'.format(load_path))


    

if __name__ == '__main__':
    args = arg_parser()
    model_path = args.saved_model_path
    load_folder = args.load_folder
    save_folder = args.save_folder
    if not os.path.exists(save_folder):
        os.mkdir(save_folder)
    cartoonize(load_folder, save_folder, model_path)
    

    
