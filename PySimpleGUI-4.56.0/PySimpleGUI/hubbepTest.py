import configparser
import os
from os.path import exists


def config_section_map(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
        except Config.DoesNotExist:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


Config = configparser.ConfigParser()
config_file_location = os.path.join(os.getcwd(), 'tommorow.ini')
if exists(config_file_location):
    Config.read(config_file_location)
else:
    cfgfile = open(config_file_location, 'w')
    cfgfile.close()


Name = config_section_map("SectionOne")['name']
Age = config_section_map("SectionOne")['age']

var = "Hello %s. You are %s years old." % (Name, Age)
print(var)
single = Config.getboolean("SectionOne", "single")
print(single)

# CLEAR CONFIG
# print(Config.sections())
for asection in Config.sections():
    Config.remove_section(asection)
# print(Config.sections())

config_file_location = os.path.join(os.getcwd(), 'next.ini')
cfgfile = open(config_file_location, 'w')
Config.add_section('Person')
Config.set('Person', 'HasEyes', "True")
Config.set('Person', 'Age', "50")
Config.write(cfgfile)
cfgfile.close()
cfgfile = open(config_file_location, 'a')
# cfgfile.write('/n')
cfgfile.close()
