# -*- coding: utf-8 -*-
"""LSTM_StockPrediction_Updated.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1g6EtPhgfxqBXIByrA5R1OyLL_DaYAmB-

## Check GPU
"""

import torch

try:
    # Get GPU name, check if it's K80
    GPU_name = torch.cuda.get_device_name()
    if GPU_name[-3:] == "K80":
        print("Get K80!")
    else:
        print("Your GPU is {}!".format(GPU_name))
except RuntimeError as e:
    if e.args == ("No CUDA GPUs are available",):
        print("You are training with CPU! ")
    else:
        print("Error message: \n", e)

"""## Mount My Drive"""

from google.colab import drive
drive.mount('/content/gdrive')
import os

# Your workspace in your drive
workspace = 'LSTM_StockPrediction_Updated'

try:
  os.chdir(os.path.join('/content/gdrive/MyDrive/', workspace))
except:
  os.mkdir(os.path.join('/content/gdrive/MyDrive/', workspace))
  os.chdir(os.path.join('/content/gdrive/MyDrive/', workspace))

# Check my current directory
os.getcwd()

"""### Download Data"""

## Download dataset from link
!gdown --id '1MbNDcFAnugKYTvme1Wq5IAloZN__9C25' --output dataset.xlsx

"""## Data Handling

### Reading Data
"""

import pandas as pd
import numpy as np

# read data
raw_data = pd.read_excel('dataset.xlsx')

# reverse the order of data
raw_data = raw_data.reindex(index=raw_data.index[::-1])

raw_data.head()

# pick out columns that we need
raw_data = raw_data [['Open', 'Close', 'Date']] 

# handel with datetime series (for plotting use)
raw_data['Date'] = pd.to_datetime(raw_data['Date'], format="%Y/%m/%d")

raw_data.head()

"""### Plotting Raw Data"""

import matplotlib.pyplot as plt

# plot original stock price data
plt.plot(raw_data['Date'],raw_data['Close'], label='Close', color='cornflowerblue')
plt.ylabel('Price') 
plt.xlabel('Date')
plt.title('Stock Price') 
plt.legend()
plt.show()

"""### Data Preprocess"""

# split data percentage
percentage = 0.8
test = raw_data[int(percentage*(len(raw_data))):(len(raw_data))]
train = raw_data[:len(raw_data)-len(test)]

test_set = test['Close']
train_set = train['Close']

print("length of raw_data: ", len(raw_data))
print("length of train_set: ", len(train_set))
print("length of test_set: ", len(test_set))

# print("train_set: ", train_set)
# print("test_set: ", test_set)

"""### Data Normalization"""

# data normalization
from sklearn.preprocessing import MinMaxScaler 
sc = MinMaxScaler(feature_range = (0, 1))

train_set= train_set.values.reshape(-1,1)
train_set_scaled = sc.fit_transform(train_set)

test_set= test_set.values.reshape(-1,1)
test_set_scaled = sc.fit_transform(test_set)

"""### Train and Test Data List"""

# set the look_back day = 5
look_back = 5

# create X_train and Y_train list
X_train = [] 
Y_train = []

for i in range(look_back,len(train_set)):
    X_train.append(train_set_scaled[i-look_back:i, 0]) 
    Y_train.append(train_set_scaled[i, 0]) 
X_train, Y_train = np.array(X_train), np.array(Y_train) 
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

print("normalized prices five days ago: ", X_train[0])
print("normalized price of the next day: ", Y_train[0])

# create X_test and Y_test list
X_test = [] 
Y_test = [] 

for i in range(look_back,len(test_set)):
    X_test.append(test_set_scaled[i-look_back:i, 0]) 
    Y_test.append(test_set_scaled[i, 0]) 
X_test, Y_test = np.array(X_test), np.array(Y_test) 
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

print("normalized prices five days ago: ", X_test[0])
print("normalized price of the next day: ", Y_test[0])

"""## Model

#### Reference from: [here](https://wenwender.wordpress.com/2019/10/18/%E5%AF%A6%E4%BD%9C%E9%80%8F%E9%81%8Elstm%E9%A0%90%E6%B8%AC%E8%82%A1%E7%A5%A8/)
"""

import keras
import tensorflow as tf 
from tensorflow import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout,BatchNormalization

keras.backend.clear_session()
regressor = Sequential()

#====================================2-layer-LSTM============================================#
# # add first LSTM layer and some Dropout regularisation
# regressor.add(LSTM(units = 100, return_sequences = True, input_shape = (X_train.shape[1], 1)))
# regressor.add(Dropout(0.2))

# # add second LSTM layer
# regressor.add(LSTM(units = 50, activation='relu'))
# regressor.add(Dense(units = 1))
#============================================================================================#

#====================================1-layer-LSTM============================================#
# add only one LSTM layer
regressor.add(LSTM(units = 100, input_shape = (X_train.shape[1], 1)))
regressor.add(Dense(units = 1))
#============================================================================================#

# change optimizer and learning rate (dafault lr = 0.001)
learning_rate = 0.001
optimizer = tf.optimizers.Adam(lr=learning_rate, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)
regressor.compile(optimizer, loss = 'mean_squared_error')

# fit model and change parameter here
epochs = 500
batch_size = 30
history = regressor.fit(X_train, Y_train, epochs = epochs, validation_data = (X_test, Y_test), batch_size = batch_size, verbose = 1)
regressor.summary()

"""### Save MSE to file"""

# evaluate the model
train_mse = regressor.evaluate(X_train, Y_train, verbose=0)
test_mse = regressor.evaluate(X_test, Y_test, verbose=0)
print('Train: %.6f, Test: %.6f' % (train_mse, test_mse))

# create a csv file to save mse record
mse_df = pd.DataFrame([[epochs,batch_size, '%.6f' % train_mse, '%.6f' % test_mse]], 
                       columns = ['epochs', 'batch_size', 'train_mse', 'test_mse'])

with open(r"updated_record_mse.csv", mode = 'a+') as f:
    mse_df.to_csv(f, header=f.tell()==0,index = False)

# save model (some warnings still not fixed)
# regressor.save('./lstm_model_epoch%d_batch%d' % (epochs, batch_size))
# reconstructed_model = keras.models.load_model('./lstm_model_epoch%d_batch%d' % (epochs, batch_size))

"""### Plotting Training Loss"""

import matplotlib.pyplot as plt

plt.plot(history.history['loss'], color='cornflowerblue', label='training loss')
plt.plot(history.history['val_loss'], color='yellowgreen', label='validation loss')

plt.title('Training Loss and Validation Loss')
plt.legend()
plt.xlabel('Epoch')
plt.ylabel('Loss')

# set y axis scale
ax = plt.gca()
ax.set_ylim([0, 0.005])

# save figure to workspace
plt.savefig('updated_plotting_training_loss_epoch%d_batch%d.png' % (epochs, batch_size), dpi=300, bbox_inches='tight')
plt.show()

"""## Predict Stock Price"""

# get total data
dataset_total = pd.concat((train['Close'], test['Close']), axis = 0)
inputs = dataset_total[len(dataset_total) - len(test) - look_back:].values
inputs = inputs.reshape(-1,1)
inputs = sc.transform(inputs)

data_for_test = []
for i in range(look_back, len(inputs)):
    data_for_test.append(inputs[i-look_back:i, 0])
data_for_test = np.array(data_for_test)
data_for_test = np.reshape(data_for_test, (data_for_test.shape[0], data_for_test.shape[1], 1))

# use regressor model to predict
predicted_stock_price = regressor.predict(data_for_test)

# sc inverse_transform return the price to original
predicted_stock_price = sc.inverse_transform(predicted_stock_price)

"""### Plotting Predicted Price"""

import matplotlib.pyplot as plt

# figure size unit is inches
plt.figure(figsize=(15,8))

# plot real stock price
plt.plot(test['Date'], test['Close'].values, color='turquoise', label='Real Stock Price')

# plot predicted stock price
plt.plot(test['Date'], predicted_stock_price, color='royalblue', label='Predicted Stock Price')

# make the X-axis text vertical
plt.xticks(rotation=90)

plt.title('Stock Price Prediction')
plt.xlabel('Time')
plt.ylabel('Stock Price')
plt.legend()

# save the figure to your workspace
plt.savefig('updated_plotting_stock_predict_epoch%d_batch%d.png' % (epochs, batch_size), dpi=300, bbox_inches='tight')
plt.show()

"""## Homework Part"""

from pandas import Series, DataFrame
import datetime

print('length of predicted_stock_price: ', len(predicted_stock_price))

# we need the last five day prices
last_fiveday_price = []
for i in range(look_back):
  price = predicted_stock_price[len(predicted_stock_price) - look_back + i]
  last_fiveday_price.append(price)

# make a new data frame for our future prediction
future_data = pd.DataFrame(pd.date_range('3/21/2022', freq='D', periods=12), columns=['Date'])
future_data["Price"] = pd.DataFrame(last_fiveday_price)

future_data.head(12)

"""### Predict Future Data"""

for j in range(7):
  new_dataset_total = future_data['Price']
  inputs = new_dataset_total[j:(j+5)].values
  inputs = inputs.reshape(-1,1)
  inputs = sc.transform(inputs)

  new_data_for_test = []
  for i in range(look_back):
      new_data_for_test.append(inputs[i])
  new_data_for_test = np.array(new_data_for_test)
  new_data_for_test = np.reshape(new_data_for_test, (new_data_for_test.shape[1], new_data_for_test.shape[0], 1))
  # print('new_data_for_test: ', new_data_for_test)

  # use regressor model to predict
  future_predicted_stock_price = regressor.predict(new_data_for_test)

  # sc inverse_transform return the price to original
  future_predicted_stock_price = sc.inverse_transform(future_predicted_stock_price)
  # future_predicted_stock_price = future_predicted_stock_price.tolist()
  # print('future_predicted_stock_price: ', future_predicted_stock_price)

  future_data.iloc[(j+5),1] = future_predicted_stock_price[0]

# show the result dataframe
future_data

# save the future stock data to csv file
future_data.to_csv('updated_future_data_epoch%d_batch%d.csv' % (epochs, batch_size))

"""### Plotting Future Price"""

import matplotlib.pyplot as plt

# figure size unit is inches
plt.figure(figsize=(15,8))

# plot future predicted stock price
plt.plot(future_data['Date'], future_data['Price'], color='indigo', label='Future Predicted Stock Price')

# make the X-axis text vertical
plt.xticks(rotation=90)

plt.title('Future Stock Price Prediction')
plt.xlabel('Time')
plt.ylabel('Stock Price')
plt.legend()

# save the figure to your workspace
plt.savefig('updated_plotting_future_predict_epoch%d_batch%d.png' % (epochs, batch_size), dpi=300, bbox_inches='tight')
plt.show()