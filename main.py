from crawers import *

if __name__ == "__main__":
    print("是否需要刷新cookie?输入Y或N。第一次打开请输入Y")
    is_refresh = input()
    print("你要看哪个博主")
    name = input()
    print("输入要下载的页数")
    pages = int(input())
    crawersinit(name, is_refresh, pages)
