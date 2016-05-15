import javalang
import os

f_path = os.path.join('/home/ubuntu/socialTrajectories/expanded_dir3/2012_1/',
                      '2012010280_1351036041_7932856',
                      'Breakout.java')
print f_path
lines = []
with open(f_path, 'r') as f:
  lines = f.readlines()

lines_str = ''.join(lines)
tokens_str = list(javalang.tokenizer.tokenize(lines_str))
  
#print '\n'.join([str(token) for token in tokens])
# for i in range(len(tokens_str)):
#   token = tokens_str[i]
#   print i, type(token), token.position
#   print token.value
#   print

def get_type(token):
  type_str = str(type(token))
  type_str = type_str.strip(">'")
  type_str = type_str.split('.')[-1]
  return type_str

def output_dict(token_dict, token_type):
  type_dict = token_dict[token_type]
  keys = type_dict.keys()
  keys.sort()
  dict_str = []
  for key in keys:
    dict_str.append(key)
    dict_str.append('>>>>>')
    dict_str.append(','.join([str(value) for value in type_dict[key]]))
  return '\n'.join(dict_str)

token_dict = {}
for i in range(len(tokens_str)):
  token = tokens_str[i]
  token_type = get_type(token)
  if token_type not in token_dict:
    token_dict[token_type] = {}
  if token.value not in token_dict[token_type]:
    token_dict[token_type][token.value] = []
  token_dict[token_type][token.value].append(token.position)

for token_type in token_dict:
  print token_type
  print output_dict(token_dict, token_type)
  print
  print
  print
