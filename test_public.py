import os, sys
sys.path.insert(0,'/app')
os.environ['SALEOR_GRAPHQL_URL']='http://fake_graphql:9001/graphql/'
from importlib import import_module
proxy = import_module('src.proxy')
print('calling public list_products')
try:
    proxy.list_products()
    print('public returned')
except Exception as e:
    print('public EXC', type(e), e)
