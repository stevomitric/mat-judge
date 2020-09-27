# Mat-judge API
Execute, evaluate and judge code in an isolated, secure enviroment, all by simple API calls.

## Overview
Mat-judge is an open source online judging system. It executes and evaluates code based on specified parameters. With easy installation, you can integrate it into your application in no time :rocket:

Features include:
* Isolated code execution
* Runtime limit
* Memory usage limit
* 10 languages support
* Token Authorization
* Worker resource distribution
* SQLite data storage
* Fast flask API response
* Full submission report
* Passive submissions
* Clientside/Serverside usage
* Request limitations and overhead management

![alt text](https://github.com/stevomitric/mat-judge/blob/master/docs/mat-judge.png?raw=true)

## Installation

Since this is built with pure python3.6, without any additional modules (except flask), you can run it on Windows, Linux or Mac. Assuming you have python 3.x and pip3 installed:

* Download or clone mat-judge [github](https://github.com/stevomitric/mat-judge) repo.
* install flask module for python3
    * `pip3 install flask`
* Run the api
    * `python3 api.py`

You're all set!

You can run `python3 api.py --help` to view command-line options for api.

By default, if you're running Linux, a single worker module will be spawned. You can take advantage of the *worker distribution* feature and run multiple workers on different machines, expanding resources and increasing maximum workload. This is recommended (and easily done) by opening an ssh tunnel and securely connecting the worker to the API.

## Development

Current version is **V1.1**, 25.09.2020.

Developed by *Stevo Mitric*, Software Engineering student at ETF, Belgrade. *stevomitric2000@gmail.com*

Project code name: *Mat-judge*

# Ussage & [Documentation](https://htmlpreview.github.io/?https://github.com/stevomitric/mat-judge/blob/master/docs/mat-judge.html "Docs")
