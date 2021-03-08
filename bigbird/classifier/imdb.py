from bigbird.core import flags
from bigbird.core import modeling
from bigbird.core import utils
from bigbird.classifier import run_classifier
import tensorflow.compat.v2 as tf
import tensorflow_datasets as tfds
from tqdm import tqdm
import sys
import numpy as np
import tensorflow

FLAGS = flags.FLAGS
if not hasattr(FLAGS, "f"): flags.DEFINE_string("f", "", "")
FLAGS(sys.argv)

tf.enable_v2_behavior()

FLAGS.data_dir = "tfds://imdb_reviews/plain_text"
FLAGS.attention_type = "block_sparse"
FLAGS.attention_probs_dropout_prob = 0.0
FLAGS.hidden_dropout_prob = 0.0
FLAGS.vocab_model_file = "gpt2"
FLAGS.num_hidden_layers = 12

bert_config = flags.as_dictionary()

model = modeling.BertModel(bert_config)
headl = run_classifier.ClassifierLossLayer(
        bert_config["num_labels"], bert_config["hidden_dropout_prob"],
        utils.create_initializer(bert_config["initializer_range"]),
        name=bert_config["scope"]+"/classifier")

@tf.function(experimental_compile=True)
def fwd_bwd(features, labels):
  with tf.GradientTape() as g:
    _, pooled_output = model(features, training=True)
    loss, log_probs = headl(pooled_output, labels, True)
  grads = g.gradient(loss, model.trainable_weights+headl.trainable_weights)
  return loss, log_probs, grads

train_input_fn = run_classifier.input_fn_builder(
        data_dir=FLAGS.data_dir,
        vocab_model_file=FLAGS.vocab_model_file,
        max_encoder_length=FLAGS.max_encoder_length,
        substitute_newline=FLAGS.substitute_newline,
        is_training=True)
dataset = train_input_fn({'batch_size': FLAGS.train_batch_size})

# inspect at a few examples
for ex in dataset.take(1):
  loss, log_probs, grads = fwd_bwd(ex[0], ex[1])
  print('Loss: ', loss.numpy(), flush=True)
ckpt_path = 'gs://bigbird-transformer/pretrain/bigbr_base/model.ckpt-0'
ckpt_reader = tf.compat.v1.train.NewCheckpointReader(ckpt_path)
model.set_weights([ckpt_reader.get_tensor(v.name[:-2]) for v in tqdm(model.trainable_weights, position=0)])

opt = tf.keras.optimizers.Adam(FLAGS.learning_rate)

train_loss = tf.keras.metrics.Mean(name='train_loss')
train_accuracy = tf.keras.metrics.CategoricalAccuracy(name='train_accuracy')


for i, ex in enumerate(tqdm(dataset.take(FLAGS.num_train_steps), position=0)):
  loss, log_probs, grads = fwd_bwd(ex[0], ex[1])
  opt.apply_gradients(zip(grads, model.trainable_weights+headl.trainable_weights))
  train_loss(loss)
  train_accuracy(tf.one_hot(ex[1], 2), log_probs)

  if i% 100 == 0:
    print('step: {} Loss = {} Accuracy = {}'.format(i, loss, train_accuracy.result().numpy()), flush=True)

@tf.function(experimental_compile=True)
def fwd_only(features, labels):
  _, pooled_output = model(features, training=False)
  loss, log_probs = headl(pooled_output, labels, False)
  return loss, log_probs

eval_input_fn = run_classifier.input_fn_builder(
        data_dir=FLAGS.data_dir,
        vocab_model_file=FLAGS.vocab_model_file,
        max_encoder_length=FLAGS.max_encoder_length,
        substitute_newline=FLAGS.substitute_newline,
        is_training=False)
eval_dataset = eval_input_fn({'batch_size': FLAGS.eval_batch_size})

eval_loss = tf.keras.metrics.Mean(name='eval_loss')
eval_accuracy = tf.keras.metrics.CategoricalAccuracy(name='eval_accuracy')

for i, ex in enumerate(tqdm(eval_dataset, position=0)):
  loss, log_probs = fwd_only(ex[0], ex[1])
  eval_loss(loss)
  eval_accuracy(tf.one_hot(ex[1], 2), log_probs)
  if i % 1000 == 0:
    print('step: {} Loss = {}  Accuracy = {}'.format(i, eval_loss.result().numpy(), eval_accuracy.result().numpy()), flush=True)

print('Loss = {}  Accuracy = {}'.format(eval_loss.result().numpy(), eval_accuracy.result().numpy()), flush=True)
