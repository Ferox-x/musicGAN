import tensorflow as tf

multidimensional_list = [[1, ], [1, 62],]

# [] # дорожки в миди файле
# [['instrument', ['notes_and_chords']]] # структура одной дорожки Инстурмент и его ноты и аккорды
# [['instrument', [['note', ['note', 'note']]]]] # структура нот и аккаордов

tensor_from_list = tf.constant(multidimensional_list)

# Print the tensor
print("Tensor from list:")
print(tensor_from_list)
