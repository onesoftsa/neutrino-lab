Neutrino Lab
==================

Neutrino Lab is a toolkit for developing and testing algorithmic trading strategies that are compatible with Neutrino API, a python framework to trade stocks, options, and futures contracts in the Brazilian financial markets. This project implements the environment that the agent interacts with, and it is composed of the order books desired, reconstruct from high-frequency tick data. Its structure is strongly influenced by [OpenAI's Gym](https://gym.openai.com/docs/) and [Kaggle Gym](https://www.kaggle.com/jeffmoser/kagglegym-api-overview) APIs.


### Install
To set up your python environment to run the code in this repository, start by following [these](https://ideaorchard.wordpress.com/2015/01/16/installing-ta-lib-ubuntu/) instructions to install TA-Lib. Then, create a new environment with Anaconda and install the dependencies.

```shell
$ conda create --name ngym36 python=3.6
$ source activate ngym36
$ pip install -r requirements.txt
```


### Run

In a terminal or command window, navigate to the top-level project directory `neutrino-lab/` (that contains this README) and run the following commands:

```shell
$ cd examples/
$ python simulation.py --viz
```
Use the flag [-h] to get the examples currently available. In another command window or tab, you can observe the behavior of the agent running:

```shell
$ cd simulate/
$ python book_viewer.py
```


### Data
An example of the datasets used in this project can be found [here](https://www.dropbox.com/s/xo5ul1h3hmtfw1k/201702.zip?dl=0).


### Docs
You can find a high-level documentation of the methods and functions of strategy API in Portuguese [here]().
