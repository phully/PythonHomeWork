#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import HttpResponse
from django.urls import reverse
from repository import models
from utils.pagination import Page


def index(request):
    """
    博客首页，展示全部博文
    :param request:  请求信息
    :param article_type: 文章类型
    :return:
    """
    if request.method == "GET":
        username = request.session.get("username", None)  # 获取session中的用户名
        user_obj = models.UserInfo.objects.filter(username=username).select_related("blog").first()  # 获取用户对象
        article_type_list = models.ArticleType.objects.all()  # 获取所有的文章类型
        current_page = int(request.GET.get("p", "1"))  # 当前页码，默认是第一页
        article_type = request.GET.get("at", request.session.get("article_type"))  # 获取用户类型,获取不到则从session中获取
        request.session["article_type"] = article_type  # 将本次查询的文章类型存入session
        if article_type and article_type != "0":  # 有类型查询条件
            article_type = int(article_type)  # 先变成整数
            article_list = models.Article.objects.filter(
                article_type=article_type).all().select_related("blog", "blog__user")  # 依据类型获取所有的文章
        else:
            article_list = models.Article.objects.all().select_related("blog", "blog__user")  # 没有类型查询条件则获取所有文章
        data_count = len(article_list)  # 文章总个数
        page_obj = Page(current_page, data_count)  # 生成分页对象
        article_list = article_list[page_obj.start:page_obj.end]  # 获取当前页的所有文章
        page_str = page_obj.page_str("/")  # 获取分页html
        return render(request, 'index.html', {
            "article_type_list": article_type_list,  # 文章类型
            'article_list': article_list,  # 文章列表
            "page_str": page_str,  # 分页HTML
            "article_type": article_type,  # 文章类型ID
            "user_obj": user_obj,  # 用户对象
        })


def home(request, site):
    """
    博主个人首页
    :param request:
    :param site: 博主的网站后缀如：http://xxx.com/wupeiqi.html
    :return:
    """
    blog_obj = models.Blog.objects.filter(site=site).select_related('user').first()
    if not blog_obj:
        return redirect('/')
    tag_list = models.Tag.objects.filter(blog=blog_obj)  # 获取博主所有的标签
    category_list = models.Category.objects.filter(blog=blog_obj)  # 获取博主所有的分类
    # date_format(create_time,"%Y-%m")
    date_list_sql = """select nid, count(nid) as num,strftime("%%Y-%%m",create_time) as ctime 
        from repository_article where blog_id = %s
        group by strftime("%%Y-%%m",create_time)
        """ % blog_obj.nid
    date_list = models.Article.objects.raw(date_list_sql)  # 获取博主文章所揽阔的月份
    article_list = models.Article.objects.filter(blog=blog_obj).order_by('-nid').all()
    current_page = int(request.GET.get("p", 1))  # 获取用户选择的页码，默认为第一页
    page_obj = Page(current_page, len(article_list))  # 获取分页对象
    page_str = page_obj.page_str("/%s.html" % site)  # 获取分页HTML
    article_list = article_list[page_obj.start:page_obj.end]  # 获取当前页数据
    return render(request, 'home.html', {
        'blog_obj': blog_obj,
        'tag_list': tag_list,
        'category_list': category_list,
        'date_list': date_list,
        'article_list': article_list,
        'page_str': page_str,
    })


def filter(request, site, condition, val):
    """
    分类显示
    :param request:
    :param site: 博客站点
    :param condition: 筛选条件
    :param val: 值
    :return:
    """
    blog_obj = models.Blog.objects.filter(site=site).select_related('user').first()
    if not blog_obj:
        return redirect('/')
    tag_list = models.Tag.objects.filter(blog=blog_obj)  # 获取博主所有的标签
    category_list = models.Category.objects.filter(blog=blog_obj)  # 获取博主所有的分类
    # date_format(create_time,"%Y-%m")
    date_list_sql = """select nid, count(nid) as num,strftime("%%Y-%%m",create_time) as ctime 
            from repository_article where blog_id = %s
            group by strftime("%%Y-%%m",create_time)
            """ % blog_obj.nid
    date_list = models.Article.objects.raw(date_list_sql)  # 获取博主文章所揽阔的月份
    template_name = "home_summary_list.html"
    if condition == 'tag':
        template_name = "home_title_list.html"
        article_list = models.Article.objects.filter(tags__title=val, blog=blog_obj).all()
    elif condition == 'category':
        article_list = models.Article.objects.filter(category__title=val, blog=blog_obj).all()
    elif condition == 'date':
        article_list = models.Article.objects.filter(blog=blog_obj).extra(
            where=['strftime("%%Y-%%m",create_time)=%s'], params=[val, ]).all()
    else:
        article_list = []
    current_page = int(request.GET.get("p", 1))  # 获取用户选择的页码，默认为第一页
    page_obj = Page(current_page, len(article_list))  # 获取分页对象
    page_str = page_obj.page_str("/%s/%s/%s.html" % (site, condition, val))  # 获取分页HTML
    article_list = article_list[page_obj.start:page_obj.end]  # 获取当前页数据
    return render(request, template_name, {
        'blog_obj': blog_obj,
        'tag_list': tag_list,
        'category_list': category_list,
        'date_list': date_list,
        'article_list': article_list,
        'page_str': page_str,
    })


def detail(request, site, nid):
    """
    博文详细页
    :param request:
    :param site:
    :param nid:
    :return:
    """
    blog_obj = models.Blog.objects.filter(site=site).select_related('user').first()
    if not blog_obj:
        return redirect('/')
    tag_list = models.Tag.objects.filter(blog=blog_obj)  # 获取博主所有的标签
    category_list = models.Category.objects.filter(blog=blog_obj)  # 获取博主所有的分类
    # date_format(create_time,"%Y-%m")
    date_list_sql = """select nid, count(nid) as num,strftime("%%Y-%%m",create_time) as ctime 
        from repository_article where blog_id = %s
        group by strftime("%%Y-%%m",create_time)
        """ % blog_obj.nid
    date_list = models.Article.objects.raw(date_list_sql)  # 获取博主文章所揽阔的月份
    # 获取文章对象
    article = models.Article.objects.filter(blog=blog_obj, nid=nid).select_related('category', 'article_detail').first()
    comment_list = models.Comment.objects.filter(article=article).select_related('reply')  # 获取评论列表
    current_page = int(request.GET.get("p", 1))  # 获取用户选择的页码，默认为第一页
    page_obj = Page(current_page, len(comment_list))  # 获取分页对象
    page_str = page_obj.page_str("/%s/%s.html" % (site, nid))  # 获取分页HTML
    comment_list = comment_list[page_obj.start:page_obj.end]  # 获取当前页数据
    return render(request, 'home_detail.html', {
        'blog_obj': blog_obj,
        'tag_list': tag_list,
        'category_list': category_list,
        'date_list': date_list,
        'article': article,
        'comment_list': comment_list,
        'page_str': page_str,
    })


def up_down(request):
    """
    点赞或者踩功能
    :param request:
    :return:
    """
    if request.method == "GET":
        return HttpResponse("ok!")
    elif request.method == "POST":
        article_id = request.POST.get("article_id")  # 获取文章ID
        username = request.POST.get("username")  # 获取用户名
        condition = request.POST.get("condition")  # 获取条件
        ret = {"status": False, "errors": None, "data": None}  # 定义返回内容
        user_obj = models.UserInfo.objects.filter(username=username).first()  # 获取点赞或者踩的用户对象
        article_obj = models.Article.objects.filter(nid=article_id).first()  # 根据文章ID获取文章对象
        up_down_obj = models.UpDown.objects.filter(user=user_obj, article_id=article_id).first()  # 根据文章和用户对象获取点赞踩对象
        if not up_down_obj:  # 对象不存在则创建
            if condition == "up":  # 点赞操作
                models.UpDown.objects.create(up=1, article_id=article_id, user=user_obj)
                article_obj.up_count += 1  # 对文章进行点赞加一
                article_obj.save()  # 保存文章对象
                ret["status"] = True
                return HttpResponse(json.dumps(ret))
            elif condition == "down":  # 踩操作
                models.UpDown.objects.create(up=0, article_id=article_id, user=user_obj)
                article_obj.down_count += 1  # 对文章进行踩加一
                article_obj.save()  # 保存文章对象
                ret["status"] = True
        else:  # 对象存在
            if condition == "up":  # 点赞操作
                if up_down_obj.up == 1:
                    pass
                else:
                    up_down_obj.up = 1  # 点赞改为True
                    up_down_obj.save()  # 保存点赞踩对象
                    article_obj.up_count += 1  # 对文章进行点赞加一
                    article_obj.down_count -= 1  # 对文章进行踩减一
                    article_obj.save()  # 保存文章对象
                    ret["status"] = True
            elif condition == "down":  # 踩操作
                if up_down_obj.up == 1:
                    up_down_obj.up = 0  # 点赞改为False
                    up_down_obj.save()  # 保存点赞踩对象
                    article_obj.up_count -= 1  # 对文章进行点赞减一
                    article_obj.down_count += 1  # 对文章进行踩加一
                    article_obj.save()  # 保存文章对象
                    ret["status"] = True
                else:
                    pass
        return HttpResponse(json.dumps(ret))
