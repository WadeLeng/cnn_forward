# Copyright 2015 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Simple, end-to-end, LeNet-5-like convolutional MNIST model example.

This should achieve a test error of 0.7%. Please keep this model as simple and
linear as possible, it is meant as a tutorial for simple convolutional models.
Run with --self_test on the command line to execute a short self-test.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import gzip
import os
import sys
import time

import numpy
from six.moves import urllib
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf


TRAINDATAFILE = "/home/yy/train_with_dataaug_.txt"
TESTDATAFILE = "/home/yy/test_with_reverse.txt"
NUM_TRAINIMAGES = 7038
NUM_TESTIMAGES = 198
IMAGE_SIZE = 112
NUM_CHANNELS = 1
PIXEL_DEPTH = 255
NUM_LABELS = 2
VALIDATION_SIZE = 700 # Size of the validation set.
SEED = 66478  # Set to None for random seed.
BATCH_SIZE = 128
NUM_EPOCHS = 25
EVAL_BATCH_SIZE = 64
EVAL_FREQUENCY = 100  # Number of steps between evaluations.


tf.app.flags.DEFINE_boolean("self_test", False, "True if running a self test.")
tf.app.flags.DEFINE_boolean('use_fp16', False,
                            "Use half floats instead of full floats if True.")
FLAGS = tf.app.flags.FLAGS


def data_type():
  """Return the type of the activations, weights, and placeholder variables."""
  if FLAGS.use_fp16:
    return tf.float16
  else:
    return tf.float32


def maybe_download(filename):
  """Download the data from Yann's website, unless it's already here."""
  if not tf.gfile.Exists(WORK_DIRECTORY):
    tf.gfile.MakeDirs(WORK_DIRECTORY)
  filepath = os.path.join(WORK_DIRECTORY, filename)
  if not tf.gfile.Exists(filepath):
    filepath, _ = urllib.request.urlretrieve(SOURCE_URL + filename, filepath)
    with tf.gfile.GFile(filepath) as f:
      size = f.Size()
    print('Successfully downloaded', filename, size, 'bytes.')
  return filepath


def extract_data(filename, num_images):
  data = []
  label = []
  with open(filename) as f:
    for line in f.readlines():
      temp_res = line.split(',')
      data.append(temp_res[:-1])
      label.append(temp_res[-1:])
    #data = data[1:]
  data = numpy.array(data).astype(numpy.float32)
  data = (data - (PIXEL_DEPTH / 2.0)) / PIXEL_DEPTH
  data = data.reshape(num_images, IMAGE_SIZE, IMAGE_SIZE, NUM_CHANNELS)
    #label = label[1:]
  label = numpy.array(label).astype(numpy.int64)
  label = label.reshape(data.shape[0],)
    #data = (data - 0.5)
    #label = numpy.zeros(NUM_LABELS * old_label.shape[0]).astype(numpy.int32)
    #label = label.reshape(old_label.shape[0], NUM_LABELS)
    #for i in range(old_label.shape[0]):
    #   label[i][old_label[i]-1] = 1

  return data, label


def extract_labels(filename, num_images):
  """Extract the labels into a vector of int64 label IDs."""
  print('Extracting', filename)
  with gzip.open(filename) as bytestream:
    bytestream.read(8)
    buf = bytestream.read(1 * num_images)
    labels = numpy.frombuffer(buf, dtype=numpy.uint8).astype(numpy.int64)
  return labels




def fake_data(num_images):
  """Generate a fake dataset that matches the dimensions of MNIST."""
  data = numpy.ndarray(
      shape=(num_images, IMAGE_SIZE, IMAGE_SIZE, NUM_CHANNELS),
      dtype=numpy.float32)
  labels = numpy.zeros(shape=(num_images,), dtype=numpy.int64)
  for image in xrange(num_images):
    label = image % 2
    data[image, :, :, 0] = label - 0.5
    labels[image] = label
  return data, labels


def error_rate(predictions, labels):
  """Return the error rate based on dense predictions and sparse labels."""
  return 100.0 - (
      100.0 *
      numpy.sum(numpy.argmax(predictions, 1) == labels) /
      predictions.shape[0])
	  
def test_error_rate(predictions, labels):
  res = numpy.argmax(predictions, 1)
  wujian = 0
  loujian = 0


  for i in range(len(res)):
    if res[i] != labels[i] and labels[i] == 0:
      wujian += 1
    if res[i] != labels[i] and labels[i] == 1:
      loujian += 1


  print(wujian)
  print(loujian)


  return 100.0 - (
    100.0 *
    numpy.sum(numpy.argmax(predictions, 1) == labels) /
    predictions.shape[0])
	
def main(argv=None):  # pylint: disable=unused-argument
  if FLAGS.self_test:
    print('Running self-test.')
    train_data, train_labels = fake_data(256)
    validation_data, validation_labels = fake_data(EVAL_BATCH_SIZE)
    test_data, test_labels = fake_data(EVAL_BATCH_SIZE)
    num_epochs = 1
  else:
    train_data, train_labels = extract_data(TRAINDATAFILE, NUM_TRAINIMAGES)
    test_data, test_labels = extract_data(TESTDATAFILE, NUM_TESTIMAGES)
    # Generate a validation set.
    validation_data = train_data[:VALIDATION_SIZE, ...]
    validation_labels = train_labels[:VALIDATION_SIZE]
    train_data = train_data[VALIDATION_SIZE:, ...]
    train_labels = train_labels[VALIDATION_SIZE:]
    num_epochs = NUM_EPOCHS
  train_size = train_labels.shape[0]

  # This is where training samples and labels are fed to the graph.
  # These placeholder nodes will be fed a batch of training data at each
  # training step using the {feed_dict} argument to the Run() call below.
  train_data_node = tf.placeholder(
      data_type(),
      shape=(BATCH_SIZE, IMAGE_SIZE, IMAGE_SIZE, NUM_CHANNELS))
  train_labels_node = tf.placeholder(tf.int64, shape=(BATCH_SIZE,))
  eval_data = tf.placeholder(
      data_type(),
      shape=(EVAL_BATCH_SIZE, IMAGE_SIZE, IMAGE_SIZE, NUM_CHANNELS))

  # The variables below hold all the trainable weights. They are passed an
  # initial value which will be assigned when we call:
  # {tf.initialize_all_variables().run()}
  conv1_weights = tf.Variable(
      tf.truncated_normal([3, 3, NUM_CHANNELS, 64],  # 5x5 filter, depth 32.
                          stddev=0.1,
                          seed=SEED, dtype=data_type()))
  conv1_biases = tf.Variable(tf.zeros([64], dtype=data_type()))
  conv2_weights = tf.Variable(tf.truncated_normal(
      [3, 3, 64, 64], stddev=0.1,
      seed=SEED, dtype=data_type()))
  conv2_biases = tf.Variable(tf.constant(0.1, shape=[64], dtype=data_type()))
  conv3_weights = tf.Variable(
      tf.truncated_normal([3, 3, 64, 128],  # 5x5 filter, depth 32.
                          stddev=0.1,
                          seed=SEED, dtype=data_type()))
  conv3_biases = tf.Variable(tf.zeros([128], dtype=data_type()))
  conv4_weights = tf.Variable(tf.truncated_normal(
      [3, 3, 128, 128], stddev=0.1,
      seed=SEED, dtype=data_type()))
  conv4_biases = tf.Variable(tf.constant(0.1, shape=[128], dtype=data_type()))

  fc1_weights = tf.Variable(tf.truncated_normal([2048, 224],
                          stddev=0.1,
                          seed=SEED,
                          dtype=data_type()))
  fc1_biases = tf.Variable(tf.constant(0.1, shape=[224], dtype=data_type()))
  fc2_weights = tf.Variable(tf.truncated_normal([224, NUM_LABELS],
                                                stddev=0.1,
                                                seed=SEED,
                                                dtype=data_type()))
  fc2_biases = tf.Variable(tf.constant(
      0.1, shape=[NUM_LABELS], dtype=data_type()))

  # We will replicate the model structure for the training subgraph, as well
  # as the evaluation subgraphs, while sharing the trainable parameters.
  def model(data, train=False):
    """The Model definition."""
    # 2D convolution, with 'SAME' padding (i.e. the output feature map has
    # the same size as the input). Note that {strides} is a 4D array whose
    # shape matches the data layout: [image index, y, x, depth].
    conv = tf.nn.conv2d(data,
                        conv1_weights,
                        strides=[1, 1, 1, 1],
                        padding='SAME')
    # Bias and rectified linear non-linearity.
    relu = tf.nn.relu(tf.nn.bias_add(conv, conv1_biases))
    # Max pooling. The kernel size spec {ksize} also follows the layout of
    # the data. Here we have a pooling window of 2, and a stride of 2.
    pool = tf.nn.max_pool(relu,
                          ksize=[1, 2, 2, 1],
                          strides=[1, 2, 2, 1],
                          padding='SAME')
    conv = tf.nn.conv2d(pool,
                        conv2_weights,
                        strides=[1, 1, 1, 1],
                        padding='SAME')
    relu = tf.nn.relu(tf.nn.bias_add(conv, conv2_biases))
    pool = tf.nn.max_pool(relu,
                          ksize=[1, 2, 2, 1],
                          strides=[1, 2, 2, 1],
                          padding='SAME')
    conv = tf.nn.conv2d(pool,
                        conv3_weights,
                        strides=[1, 1, 1, 1],
                        padding='SAME')
    relu = tf.nn.relu(tf.nn.bias_add(conv, conv3_biases))
    pool = tf.nn.max_pool(relu,
                          ksize=[1, 2, 2, 1],
                          strides=[1, 2, 2, 1],
                          padding='SAME')

    conv = tf.nn.conv2d(pool,
                        conv4_weights,
                        strides=[1, 1, 1, 1],
                        padding='SAME')
    relu = tf.nn.relu(tf.nn.bias_add(conv, conv4_biases))

    pool = tf.nn.max_pool(relu,
                          ksize=[1, 4, 4, 1],
                          strides=[1, 4, 4, 1],
                          padding='SAME')

    # Reshape the feature map cuboid into a 2D matrix to feed it to the
    # fully connected layers.
    pool_shape = pool.get_shape().as_list()
    reshape = tf.reshape(
        pool,
        [pool_shape[0], pool_shape[1] * pool_shape[2] * pool_shape[3]])
    # Fully connected layer. Note that the '+' operation automatically
    # broadcasts the biases.
    hidden = tf.nn.relu(tf.matmul(reshape, fc1_weights) + fc1_biases)
    # Add a 50% dropout during training only. Dropout also scales
    # activations such that no rescaling is needed at evaluation time.
    if train:
      hidden = tf.nn.dropout(hidden, 0.5, seed=SEED)
    return tf.matmul(hidden, fc2_weights) + fc2_biases

  # Training computation: logits + cross-entropy loss.
  logits = model(train_data_node, True)
  loss = tf.reduce_mean(tf.nn.sparse_softmax_cross_entropy_with_logits(
      logits, train_labels_node))

  # L2 regularization for the fully connected parameters.
  regularizers = (tf.nn.l2_loss(fc1_weights) + tf.nn.l2_loss(fc1_biases) +
                  tf.nn.l2_loss(fc2_weights) + tf.nn.l2_loss(fc2_biases))
  # Add the regularization term to the loss.
  loss += 5e-4 * regularizers

  # Optimizer: set up a variable that's incremented once per batch and
  # controls the learning rate decay.
  batch = tf.Variable(0, dtype=data_type())
  # Decay once per epoch, using an exponential schedule starting at 0.01.
  learning_rate = tf.train.exponential_decay(
      0.01,                # Base learning rate.
      batch * BATCH_SIZE,  # Current index into the dataset.
      train_size,          # Decay step.
      0.95,                # Decay rate.
      staircase=True)
  # Use simple momentum for the optimization.
  optimizer = tf.train.MomentumOptimizer(learning_rate,
                                         0.9).minimize(loss,
                                                       global_step=batch)

  # Predictions for the current training minibatch.
  train_prediction = tf.nn.softmax(logits)

  # Predictions for the test and validation, which we'll compute less often.
  eval_prediction = tf.nn.softmax(model(eval_data))

  # Small utility function to evaluate a dataset by feeding batches of data to
  # {eval_data} and pulling the results from {eval_predictions}.
  # Saves memory and enables this to run on smaller GPUs.
  def eval_in_batches(data, sess):
    """Get all predictions for a dataset by running it in small batches."""
    size = data.shape[0]
    if size < EVAL_BATCH_SIZE:
      raise ValueError("batch size for evals larger than dataset: %d" % size)
    predictions = numpy.ndarray(shape=(size, NUM_LABELS), dtype=numpy.float32)
    for begin in xrange(0, size, EVAL_BATCH_SIZE):
      end = begin + EVAL_BATCH_SIZE
      if end <= size:
        predictions[begin:end, :] = sess.run(
            eval_prediction,
            feed_dict={eval_data: data[begin:end, ...]})
      else:
        batch_predictions = sess.run(
            eval_prediction,
            feed_dict={eval_data: data[-EVAL_BATCH_SIZE:, ...]})
        predictions[begin:, :] = batch_predictions[begin - size:, :]
    return predictions

  # Create a local session to run the training.
  start_time = time.time()
  with tf.Session() as sess:
    # Run all the initializers to prepare the trainable parameters.
    tf.initialize_all_variables().run()
    print('Initialized!')
    # Loop through training steps.
    #saver = tf.train.Saver()
    for step in xrange(int(num_epochs * train_size) // BATCH_SIZE):
      # Compute the offset of the current minibatch in the data.
      # Note that we could use better randomization across epochs.
      offset = (step * BATCH_SIZE) % (train_size - BATCH_SIZE)
      batch_data = train_data[offset:(offset + BATCH_SIZE), ...]
      batch_labels = train_labels[offset:(offset + BATCH_SIZE)]
      # This dictionary maps the batch data (as a numpy array) to the
      # node in the graph it should be fed to.
      feed_dict = {train_data_node: batch_data,
                   train_labels_node: batch_labels}
      # Run the graph and fetch some of the nodes.
      _, l, lr, predictions = sess.run(
          [optimizer, loss, learning_rate, train_prediction],
          feed_dict=feed_dict)
      if step % EVAL_FREQUENCY == 0:
        elapsed_time = time.time() - start_time
        start_time = time.time()
        print('Step %d (epoch %.2f), %.1f ms' %
              (step, float(step) * BATCH_SIZE / train_size,
               1000 * elapsed_time / EVAL_FREQUENCY))
        print('Minibatch loss: %.3f, learning rate: %.6f' % (l, lr))
        print('Minibatch error: %.1f%%' % error_rate(predictions, batch_labels))
        print('Validation error: %.1f%%' % error_rate(
            eval_in_batches(validation_data, sess), validation_labels))
        sys.stdout.flush()
    # Finally print the result!
    test_error = test_error_rate(eval_in_batches(test_data, sess), test_labels)
    #save_path = saver.save(sess, "/home/ylp/model.ckpt")
    print('Test error: %.1f%%' % test_error)

    conv1_weights = sess.run(conv1_weights)
    conv1_biases = sess.run(conv1_biases)
    conv2_weights = sess.run(conv2_weights)
    conv2_biases = sess.run(conv2_biases)
    conv3_weights = sess.run(conv3_weights)
    conv3_biases = sess.run(conv3_biases)
    conv4_weights = sess.run(conv4_weights)
    conv4_biases = sess.run(conv4_biases)
    fc1_weights = sess.run(fc1_weights)
    fc1_biases = sess.run(fc1_biases)
    fc2_weights = sess.run(fc2_weights)
    fc2_biases = sess.run(fc2_biases)

    with open("/home/yy/CNN/Model_4_dataaug.txt", "w") as f:
      for i in range(64):
        for j in range(3):
          for k in range(3):
            if i==63 and j==2 and k==2:
              f.write(str(conv1_weights[j][k][0][i]))
            else:
              f.write(str(conv1_weights[j][k][0][i]) + ",")

      f.write('\n')

      for i in range(64):
        if i==63:
          f.write(str(conv1_biases[i]))
        else:
          f.write(str(conv1_biases[i]) + ",")

      f.write('\n')

      for i in range(64):
        for q in range(64):
          for j in range(3):
            for k in range(3):
              if i==63 and j==2 and k==2 and q==63:
                f.write(str(conv2_weights[j][k][q][i]))
              else:
                f.write(str(conv2_weights[j][k][q][i]) + ",")

      f.write('\n')

      for i in range(64):
        if i==63:
          f.write(str(conv2_biases[i]))
        else:
          f.write(str(conv2_biases[i]) + ",")

      f.write('\n')

      for i in range(128):
        for q in range(64):
          for j in range(3):
            for k in range(3):
              if i==127 and j==2 and k==2 and q==63:
                f.write(str(conv3_weights[j][k][q][i]))
              else:
                f.write(str(conv3_weights[j][k][q][i]) + ",")

      f.write('\n')

      for i in range(128):
        if i==127:
          f.write(str(conv3_biases[i]))
        else:
          f.write(str(conv3_biases[i]) + ",")

      f.write('\n')

      for i in range(128):
        for q in range(128):
          for j in range(3):
            for k in range(3):
              if i==127 and j==2 and k==2 and q==127:
                f.write(str(conv4_weights[j][k][q][i]))
              else:
                f.write(str(conv4_weights[j][k][q][i]) + ",")

      f.write('\n')

      for i in range(128):
        if i==127:
          f.write(str(conv4_biases[i]))
        else:
          f.write(str(conv4_biases[i]) + ",")

      f.write('\n')


      for i in range(2048):
        for j in range(224):
          if i==2047 and j==223:
            f.write(str(fc1_weights[i][j]))
          else:
            f.write(str(fc1_weights[i][j]) + ",")

      f.write('\n')

      for i in range(224):
        if i == 223:
          f.write(str(fc1_biases[i]))
        else:
          f.write(str(fc1_biases[i]) + ",")

      f.write('\n')

      for i in range(224):
        for j in range(NUM_LABELS):
          if j==NUM_LABELS-1 and i==223:
            f.write(str(fc2_weights[i][j]))
          else:
            f.write(str(fc2_weights[i][j]) + ",")
      f.write('\n')

      for i in range(NUM_LABELS):
        if i == NUM_LABELS-1:
          f.write(str(fc2_biases[i]))
        else:
          f.write(str(fc2_biases[i]) + ",")

    if FLAGS.self_test:
      print('test_error', test_error)
      assert test_error == 0.0, 'expected 0.0 test_error, got %.2f' % (
          test_error,)


if __name__ == '__main__':
  tf.app.run()