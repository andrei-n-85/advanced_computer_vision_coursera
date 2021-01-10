import urllib.request
import os
import zipfile
import random
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers
from tensorflow.keras import Model
from tensorflow.keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.optimizers import RMSprop
from shutil import copyfile

import matplotlib.image  as mpimg
import matplotlib.pyplot as plt
import numpy as np
from keras.preprocessing import image


def split_data(SOURCE, TRAINING, TESTING, SPLIT_SIZE):
    files = []
    for filename in os.listdir(SOURCE):
        file = SOURCE + filename
        if os.path.getsize(file) > 0:
            files.append(filename)
        else:
            print(filename + " is zero length, so ignoring.")

    training_length = int(len(files) * SPLIT_SIZE)
    testing_length = int(len(files) - training_length)
    shuffled_set = random.sample(files, len(files))
    training_set = shuffled_set[0:training_length]
    testing_set = shuffled_set[training_length:]

    for filename in training_set:
        this_file = SOURCE + filename
        destination = TRAINING + filename
        copyfile(this_file, destination)

    for filename in testing_set:
        this_file = SOURCE + filename
        destination = TESTING + filename
        copyfile(this_file, destination)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # data_url = "https://download.microsoft.com/download/3/E/1/3E1C3F21-ECDB-4869-8368-6DEBA77B919F/kagglecatsanddogs_3367a.zip"
    # data_file_name = "catsdogs.zip"
    # download_dir = './'
    # urllib.request.urlretrieve(data_url, data_file_name)
    # zip_ref = zipfile.ZipFile(data_file_name, 'r')
    # zip_ref.extractall(download_dir)
    # zip_ref.close()
    # print("Number of cat images:", len(os.listdir('./PetImages/Cat/')))
    # print("Number of dog images:", len(os.listdir('./PetImages/Dog/')))
    # try:
    #     os.mkdir('./cats-v-dogs')
    #     os.mkdir('./cats-v-dogs/training')
    #     os.mkdir('./cats-v-dogs/testing')
    #     os.mkdir('./cats-v-dogs/training/cats')
    #     os.mkdir('./cats-v-dogs/training/dogs')
    #     os.mkdir('./cats-v-dogs/testing/cats')
    #     os.mkdir('./cats-v-dogs/testing/dogs')
    # except OSError:
    #     pass
    CAT_SOURCE_DIR = "./PetImages/Cat/"
    TRAINING_CATS_DIR = "./cats-v-dogs/training/cats/"
    TESTING_CATS_DIR = "./cats-v-dogs/testing/cats/"
    DOG_SOURCE_DIR = "./PetImages/Dog/"
    TRAINING_DOGS_DIR = "./cats-v-dogs/training/dogs/"
    TESTING_DOGS_DIR = "./cats-v-dogs/testing/dogs/"

    split_size = .9
    split_data(CAT_SOURCE_DIR, TRAINING_CATS_DIR, TESTING_CATS_DIR, split_size)
    split_data(DOG_SOURCE_DIR, TRAINING_DOGS_DIR, TESTING_DOGS_DIR, split_size)
    print("Number of training cat images", len(os.listdir('./cats-v-dogs/training/cats/')))
    print("Number of training dog images", len(os.listdir('./cats-v-dogs/training/dogs/')))
    print("Number of testing cat images", len(os.listdir('./cats-v-dogs/testing/cats/')))
    print("Number of testing dog images", len(os.listdir('./cats-v-dogs/testing/dogs/')))

    TRAINING_DIR = "./cats-v-dogs/training/"
    # Experiment with your own parameters to reach 99.9% validation accuracy or better
    train_datagen = ImageDataGenerator(rescale=1. / 255,
                                       rotation_range=40,
                                       width_shift_range=0.2,
                                       height_shift_range=0.2,
                                       shear_range=0.2,
                                       zoom_range=0.2,
                                       horizontal_flip=True,
                                       fill_mode='nearest')
    train_generator = train_datagen.flow_from_directory(TRAINING_DIR,
                                                        batch_size=100,
                                                        class_mode='binary',
                                                        target_size=(150, 150))

    VALIDATION_DIR = "./cats-v-dogs/testing/"

    validation_datagen = ImageDataGenerator(rescale=1. / 255)
    validation_generator = validation_datagen.flow_from_directory(VALIDATION_DIR,
                                                                  batch_size=100,
                                                                  class_mode='binary',
                                                                  target_size=(150, 150))

    weights_url = "https://storage.googleapis.com/mledu-datasets/inception_v3_weights_tf_dim_ordering_tf_kernels_notop.h5"
    weights_file = "inception_v3.h5"
    urllib.request.urlretrieve(weights_url, weights_file)

    # Instantiate the model
    pre_trained_model = InceptionV3(input_shape=(150, 150, 3),
                                    include_top=False,
                                    weights=None)

    # load pre-trained weights
    pre_trained_model.load_weights(weights_file)

    # freeze the layers
    for layer in pre_trained_model.layers:
        layer.trainable = False

    # pre_trained_model.summary()

    last_layer = pre_trained_model.get_layer('mixed7')
    print('last layer output shape: ', last_layer.output_shape)
    last_output = last_layer.output

    # Flatten the output layer to 1 dimension
    x = layers.Flatten()(last_output)
    # Add a fully connected layer with 1,024 hidden units and ReLU activation
    x = layers.Dense(1024, activation='relu')(x)
    # Add a final sigmoid layer for classification
    x = layers.Dense(1, activation='sigmoid')(x)

    model = Model(pre_trained_model.input, x)

    # compile the model
    model.compile(optimizer=RMSprop(lr=0.0001),
                  loss='binary_crossentropy',
                  metrics=['acc'])

    # train the model (adjust the number of epochs from 1 to improve performance)
    history = model.fit(
        train_generator,
        validation_data=validation_generator,
        epochs=2,
        verbose=1)

    # -----------------------------------------------------------
    # Retrieve a list of list results on training and test data
    # sets for each training epoch
    # -----------------------------------------------------------
    acc = history.history['acc']
    val_acc = history.history['val_acc']
    loss = history.history['loss']
    val_loss = history.history['val_loss']

    epochs = range(len(acc))  # Get number of epochs

    # ------------------------------------------------
    # Plot training and validation accuracy per epoch
    # ------------------------------------------------
    plt.plot(epochs, acc, 'r', "Training Accuracy")
    plt.plot(epochs, val_acc, 'b', "Validation Accuracy")
    plt.title('Training and validation accuracy')
    plt.figure()

    uploaded = files.upload()

    for fn in uploaded.keys():

        # predicting images
        path = '/content/' + fn
        img = image.load_img(path, target_size=(150, 150))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)

        image_tensor = np.vstack([x])
        classes = model.predict(image_tensor)
        print(classes)
        print(classes[0])
        if classes[0] > 0.5:
            print(fn + " is a dog")
        else:
            print(fn + " is a cat")




