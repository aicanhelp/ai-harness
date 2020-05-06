# AI Harness

## Introduction
This project would like to supply some convenient tools for the machine learning and deep learning.
Current features:  
- XMLConfiguration: for loading a configuration defined in xml files into a Python Object
- Arguments: Mapping a Python Object to the arguments of argparse 
- inspector: Some convenient method for class/object  
- executors: Some convenient ProcessExecutor
- fileutils: DirectoryNavigator, FileReadPipeLine
- others:

## Log
- 2019.4.18, version: 0.3.0: Added distributed training tools for python  
- 2019.4.23, version: 0.3.5: Added a Json file Reader
- 2019.4.24, version: 0.3.6: Added a data utils for processing data
- 2019.4.26, version: 0.3.7 Added a data utils for processing data for zip file
- 2019.4.28, version: 0.3.8 Added QueueExecutor

## Examples
### 1. XMLConfiguration
##### (1) Define the configuration in xml file like:
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<configuration>
    <arg name="name" default="TestName" help="Name Test Help"/>
    <arg name="age" default="20" help="Age Test Help"/>
    <group name="address">
        <arg name="home" default="shanghai" help="Home test Help"/>
        <arg name="phone" default="136" help="Phone test Help"/>
    </group>
    <group name="education">
        <arg name="school" default="beijing" help="school test Help"/>
        <arg name="grade" default="master" help="grade test Help"/>
    </group>
</configuration>
``` 
you can define multiple xml configuration files, and if the name is same, the value of the later will cover the previous. 
#### (3) Define the configuration class like: 
```
from aiharness.configuration import configclass,field

@configclass
class Address:
    phone: int = field(139, "phone help")
    home: str = field("beijing", "phone help")


@configclass
class Education:
    school: str = field('ustb', "phone help")
    grade: str = field("master", "phone help")


@configclass
class Config:
    name: str = field("test", "name help")
    age: str = field(10, "age help")
    address: Address = Address()
    education: Education = Education()
```
#### (3) Load the xml configuration into python object as folling:
```
from aiharness.configuration import XmlConfiguration

config:Config=XmlConfiguration(Config).load(['configuration1.xml','configuration2.xml'])
```
### Arguments Example
Generally, we use argparse as following:
```
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--name",default='TEST',help='name help')
parser.add_argument("--age",default=18,help='age help')
arguments=parser.parse_args()
```
And you can got a arguments object.

Here give an example showing how to load a xml configuration and set to argparse arguments and to parse the arguments into a object you defined.
And here the Config Class and 'configuration.xml' are same with those of the Configuration example.

Firstly, in fact, the Config Class instead of the codes of 'add_argument' of the argparse.ArgumentParser.
Secondly, you can put the configuration into a xml file so that you can change it conveniently.

```
from aiharness.configuration import  Arguments, XmlConfiguration

config: Config = XmlConfiguration(Config).load(['configuration.xml'])
arguments = Arguments(config)
config: Config = arguments.parse()

```

