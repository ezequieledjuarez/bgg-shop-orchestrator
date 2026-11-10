import os, traceback, sys
sys.path.insert(0,'/app')
print('PYTHONPATH set')
os.environ['SALEOR_GRAPHQL_URL']='http://fake_graphql:9001/graphql/'
from importlib import import_module
proxy = import_module('src.proxy')
print('proxy file:', proxy.__file__)
try:
    proxy.list_products(token='Bearer testtoken123')
    print('list_products returned')
except Exception as e:
    print('EXC:', type(e), e)
    traceback.print_exc()
print('DONE')
