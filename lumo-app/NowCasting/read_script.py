import tensorflow as tf

filenames = ['C:/Users/saile/Documents/GOES/output/2020-03-15/2020-03-15_15842627.tfrecord.gz']
raw_dataset = tf.data.TFRecordDataset(filenames, compression_type="GZIP")
image_feature_description = {name: tf.io.FixedLenFeature([], dtype)
             for name, dtype in [
               ("radar", tf.string), ("sample_prob", tf.float32),
               ("lonmin", tf.int64), ("lonmax", tf.int64),
               ("latmin", tf.int64), ("latmax", tf.int64),
               ("end_time_timestamp", tf.int64),
             ]}
def _parse_image_function(example_proto):
  # Parse the input tf.train.Example proto using the dictionary above.
  content = tf.io.parse_single_example(example_proto, image_feature_description)
  raw_image = content['radar']
  feature = tf.io.parse_tensor(raw_image, out_type=tf.float64)
  feature = tf.reshape(feature, shape=(24,256,256,1))
  return (feature, content['latmin'])

parsed_image_dataset = raw_dataset.map(_parse_image_function)
for sample in parsed_image_dataset.take(1):
  print(sample[0].shape)
print(parsed_image_dataset)