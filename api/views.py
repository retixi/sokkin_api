from django.shortcuts import render
from django.http import HttpResponse
import pymongo,json,jwt,random,re
client = pymongo.MongoClient("www.zhihuazhang.net",27017)
db = client['retixi']
db.authenticate('retixi','password')
pin_col = db['pin']
category_col = db['category']
item_col = db['item']

def auth_func(request):
    try:
        accesstoken = request.META.get('HTTP_AUTHORIZATION')
        phone_req = jwt.decode(accesstoken,'pin')['phone']
        user_find = pin_col.find_one({'phone':phone_req})
        if user_find != None:
            return user_find
        else:
            return False
    except:
            return False

def verify(request):
    if request.method == "POST":
        phone = json.loads(request.readline())['phone']
        pin = str(random.randrange(100000000,999999999))
        print(pin)
        pin_col.insert_one({'phone':phone,'pin':pin})
        res_body = json.dumps({"phone":phone,"pin":pin},ensure_ascii=False)
        res = HttpResponse(res_body)
        return HttpResponse(res)

def pin(request):
    if request.method == "POST":
        user = json.loads(request.readline())
        user_find = pin_col.find_one({'phone': user['phone']})
        if user_find != None:
            if user_find['pin'] == user['pin']:
                accesstoken = jwt.encode({'phone': user['phone']}, 'pin')
                body = {
                    "accessToken": accesstoken.decode(),
                }
                res_body = json.dumps(body)
                res = HttpResponse(res_body)
            else:
                body = {
                    "message": "pin码错误"
                }
                res_body = json.dumps(body,ensure_ascii=False)
                res = HttpResponse(res_body)
                # res.status_code = 401
        else:
            body = {
                "message": "电话号码不存在"
            }
            res_body = json.dumps(body,ensure_ascii=False)
            res = HttpResponse(res_body)
            # res.status_code = 401
        return res

def categories(request):
    if request.method == "GET":
        if auth_func(request):
            cate_list = []
            for i in category_col.find():
                i.pop('_id')
                cate_list.append(i)
            res_body = json.dumps(cate_list,ensure_ascii=False)
            res = HttpResponse(res_body)
            return res
        else:
            res = HttpResponse("用户未认证")
            return res

def confirms(request):
    if request.method =="GET":
        if auth_func(request):
            cid = int(request.path.split('/')[-2])
            cate = category_col.find_one({"id":cid})
            if cate != None:
                res_cate = {
                    "content":cate['content'],
                    "category":cate['name']
                }
                res_body = json.dumps(res_cate,ensure_ascii=False)
                res = HttpResponse(res_body)
            else:
                res = HttpResponse("id不存在")
        else:
            res = HttpResponse('用户没有权限')
        return res

def suggestions(request):
    if request.method == "GET":
        if auth_func(request):
            cate_id = int(request.GET["category"])
            title_keyword = request.GET["keyword"]
            cate_name = category_col.find_one({"id":cate_id})['name']
            find_result = item_col.find({"category": cate_name,
                                         "title":re.compile(title_keyword,re.IGNORECASE)
                                         })
            find_list = []
            for each in find_result:
                find_list.append({"name":each['title']})
            if find_list == []:
                res = HttpResponse("没有在该品类查询到相关物品")
            else:
                res_body = json.dumps(find_list,ensure_ascii=False)
                res = HttpResponse(res_body)
        else:
            res = HttpResponse('用户没有权限')
        return res

def items(request):
    if auth_func(request):
        id_find = int(request.path.split('/')[-2])
        item_find = item_col.find_one({"id": id_find})
        if item_find == None:
            res = HttpResponse('商品id不存在')
        else:
            if request.method == "GET":
                    item_find.pop('_id')
                    res_body = json.dumps(item_find, ensure_ascii=False)
                    res = HttpResponse(res_body)
            elif request.method == "PUT":
                item_update = json.loads(request.readline())
                item_col.find_one_and_update({"id":id_find},{"$set":item_update})
                body = item_col.find_one({"id":id_find})
                body.pop('_id')
                res_body = json.dumps(body,ensure_ascii=False)
                res = HttpResponse(res_body)
    else:
        res = HttpResponse("用户未认证")
    return res

def sell(request):
    if request.method == "PUT":
        id_find = int(request.path.split('/')[-2])
        item_find = item_col.find_one({"id": id_find})
        if item_find == None:
            res = HttpResponse('商品id不存在')
        else:
            item_col.find_one_and_update({"id": id_find}, {"$set": {"soldout":1}})
            res = HttpResponse('商品售出')
            res.status_code = 204
        return res

def myitem(request):
    if request.method == "GET":
        if(auth_func(request)):
            user = auth_func(request)
            try:
                collection = user['collection']
            except:
                collection = []
            assessed = []
            assessing = []
            try:
                for each in user['assessedid']:
                    item_assessed = item_col.find_one({"id":each})
                    item_assessed.pop('_id')
                    assessed.append(item_assessed)
            except:
                pass
            try:
                for each in user['assessingid']:
                    item_assessing = item_col.find_one({"id": each})
                    item_assessing.pop('_id')
                    assessing.append(item_assessing)
            except:
                pass
            body = {
                "assessed":assessed,
                "assessing":assessing,
                "collection":collection
            }
            res_body = json.dumps(body,ensure_ascii=False)
            res = HttpResponse(res_body)
        else:
            res = HttpResponse('用户无权限')
        return res

def notices(request):
    if request.method =="GET":
        user = auth_func(request)
        if user:
            try:
                mynotices = user['notices']
            except KeyError:
                mynotices = []
            res_body = json.dumps(mynotices,ensure_ascii=False)
            res = HttpResponse(res_body)
        else:
            res = HttpResponse('无权限')
        return res

def profile(request):
    user = auth_func(request)
    if user:
        if request.method == "GET":
            try:
                myprofile = user['profile']
            except KeyError:
                myprofile = []
            res_body = json.dumps(myprofile,ensure_ascii=False)
            res = HttpResponse(res_body)
        elif request.method == "PUT":
            accesstoken = request.META.get('HTTP_AUTHORIZATION')
            phone_req = jwt.decode(accesstoken, 'pin')['phone']
            profile_update = json.loads(request.readline())
            try:
                user['profile'].update(profile_update)
            except:
                user['profile'] = profile_update
            pin_col.find_one_and_update({"phone":phone_req}, {"$set": user})
            body = user['profile']
            res_body = json.dumps(body, ensure_ascii=False)
            res = HttpResponse(res_body)
    else:
        res = HttpResponse('无权限')
    return res


# Create your views here.
'''
def auth_func(request):
    try:
        accesstoken = request.META.get('HTTP_AUTHORIZATION')
        uid_req = jwt.decode(accesstoken,'secret')['uid']
        user_find = user_col.find_one({'uid':uid_req})
        if user_find != None:
            return user_find
        else:
            return False
    except:
            return False

def login(request):
    if request.method == "POST":
        user = json.loads(request.readline())
        user_find = user_col.find_one({'uid':user['uid']})
        if user_find != None:
            if user_find['password'] == user['password']:
                accesstoken = jwt.encode({'uid': user['uid']}, 'secret')
                user_find['_id'] = str(user_find['_id'])
                body = {
            "accessToken": accesstoken.decode(),
            "user": user_find
        }
                res_body = json.dumps(body)
                res = HttpResponse(res_body)
            else:
                body = {
                    "status": 401,
                    "message": "IDとパスワードが一致しません。"
                }
                res_body = json.dumps(body)
                res = HttpResponse(res_body)
                #res.status_code = 401
        else:
            body = {
                "status": 401,
                "message": "用户不存在"
            }
            res_body = json.dumps(body)
            res = HttpResponse(res_body)
            #res.status_code = 401
        return res

def logout(request):
    if auth_func(request):
        res = HttpResponse('用户{}已登出'.format(auth_func(request)['uid']))
        res['AUTHORIZATION'] = None
        return res
    else:
        return HttpResponse('用户已登出')

def users(request):
    if request.method == "POST":
        user = json.loads(request.readline())
        user_find = user_col.find_one({'uid':user['uid']})
        if user_find == None:
            user['inviting'] = []
            user['invited'] = []
            user['friends'] = []
            user_col.insert_one(user)
            user_find = user_col.find_one({'uid':user['uid']})
            user['_id'] = str(user_find['_id'])
            accesstoken = jwt.encode({'uid':user['uid']},'secret')
            body = {
                "accessToken": accesstoken.decode(),
                'user': user
            }
            res_body = json.dumps(body)
            res = HttpResponse(res_body)
        else:
            body = {
              "status": 409,
              "message": "IDがすでに登録済みです。"
            }
            res_body = json.dumps(body)
            res = HttpResponse(res_body)
            res.status_code = 409
        return res
    elif request.method == "GET":
        if auth_func(request):
            userid_group = request.GET['uids'].split('%')
            user_group = []
            for each in userid_group:
                user_find = user_col.find_one({'uid':each})
                if user_find != None:
                    user_find.pop('_id')
                    user_group.append(user_find)
            body = json.dumps(user_group)
            return HttpResponse(body)
        else:
            return HttpResponse('用户未登录')

def user_sel(request):
    if auth_func(request):
        uid = request.path.split('/')[-1]
        user_find = user_col.find_one({'uid':uid})
        if user_find != None:
            body = [
                  {
                    "_id": str(user_find['_id']),
                    "name": user_find['name'],
                    "uid": user_find['uid'],
                    "avatar": 'avatar'
                  },
                  {
                    "_id": str(user_find['_id']),
                    "name": user_find['name'],
                    "uid": user_find['uid'],
                  }
                ]
            res_body = json.dumps(body)
            res = HttpResponse(res_body)
        else:
            res = HttpResponse('无此用户')
    else:
        res = HttpResponse('用户未登录')
        res.status_code = 401
    return res

def delete(request):
    if auth_func(request):
        if request.method =='POST':
            uid = json.loads(request.readline())['uid']
            user_find = user_col.find_one({'uid': uid})
            if user_find != None:
                user_col.remove({'uid':uid})
                password = user_find['password']
                str1 = '删除了{}的用户信息,他的密码是{}'.format(uid,password)
                res = HttpResponse(str1)
            else:
                res = HttpResponse('无此用户')
    else:
        res = HttpResponse('用户未登录')
        res.status_code = 401
    return res

def user(request):
    if auth_func(request):
        user = auth_func(request)
        if request.method == "GET":
            user['_id'] = str(user['_id'])
            res_body = json.dumps(user)
            res = HttpResponse(res_body)
        elif request.method == "PATCH":
            update_info = json.loads(request.readline())
            print(update_info)
            for key in update_info:
                user[key] = update_info[key]
            user_col.update({'uid':user['uid']},user)
            user['_id'] = str(user['_id'])
            res_body = json.dumps(user)
            res = HttpResponse(res_body)
    else:
        res = HttpResponse('用户未登录')
        res.status_code = 401
    return res

def inviting(request):
    if auth_func(request):
        user_inviting = auth_func(request)
        user_invited_uid = request.path.split('/')[-1]
        try:
            if user_invited_uid in list(each['uid'] for each in user_inviting['friends']):
                print(list(each['uid'] for each in user_inviting['friends']))
                return HttpResponse('你们已经是好友')
        except KeyError:
            pass
        try:
            if user_invited_uid in list(each['uid'] for each in user_inviting['invited']):
                return HttpResponse('对方已经邀请你了')
        except KeyError:
            pass
        if user_inviting["uid"] == user_invited_uid:
            res = HttpResponse('被邀请人是你自己')
        else:
            if request.method == "PUT":
                user_invited = user_col.find_one({"uid":user_invited_uid})
                if user_invited != None:
                    if 'inviting' in user_inviting.keys():
                        if {"uid":user_invited['uid']} not in user_inviting['inviting']:
                            user_inviting['inviting'].append({"uid":user_invited_uid})
                    else:
                        user_inviting['inviting'] = [{"uid":user_invited_uid}]
                    if "invited" in user_invited:
                        if {"uid":user_inviting['uid']} not in user_invited['invited']:
                            user_invited["invited"].append({"uid":user_inviting["uid"]})
                    else:
                        user_invited["invited"] = [{"uid":user_inviting["uid"]}]
                    user_col.update({'uid':user_inviting['uid']},user_inviting)
                    user_col.update({'uid':user_invited['uid']},user_invited)
                    user_inviting['_id'] = str(user_inviting["_id"])

                    res = HttpResponse(json.dumps(user_inviting))
                else:
                    res = HttpResponse('没有此用户')
    else:
        res = HttpResponse('用户未登录')
        res.status_code = 401
    return res

def friend(request):
    if auth_func(request):
        user = auth_func(request)
        user_friend_uid = request.path.split('/')[-1]
        user_friend = user_col.find_one({"uid":user_friend_uid})
        if user_friend_uid in list(each['uid'] for each in user['friends']):
            return HttpResponse('你们已经是好友')
        if 'invited' in user_friend.keys():
            if {'uid':user['uid']} in user_friend['inviting']:
                user_friend_add = {
                    "_id": str(user_friend['_id']),
                    "name": user_friend["name"],
                    "uid": user_friend["uid"],
                }
                user_add = {
                    "_id": str(user['_id']),
                    "name": user["name"],
                    "uid": user["uid"],
                }
                u_friendlist = []
                f_friendlist = []
                try:
                    u_friendlist.extend(user['friends'])
                except KeyError:
                    pass
                try:
                    f_friendlist.extend(user_friend['friends'])
                except KeyError:
                    pass
                uid_list = [each['uid'] for each in u_friendlist]
                if user_friend_add['uid'] not in uid_list:
                    u_friendlist.append(user_friend_add)
                    f_friendlist.append(user_add)
                    user['friends'] = u_friendlist
                    user_friend['friends'] = f_friendlist
                    user['invited'].remove({"uid":user_friend_add["uid"]})
                    user_friend['inviting'].remove({"uid":user_add["uid"]})
                    user_col.update({'uid':user['uid']},user)
                    user_col.update({'uid':user_friend['uid']},user_friend)
                user['_id'] = str(user['_id'])
                res = HttpResponse(json.dumps(user))
            else:
                res = HttpResponse('此用户暂未被邀请')
        else:
            res = HttpResponse('该用户没有被任何人邀请')
    else:
        res = HttpResponse('用户未登录')
        res.status_code = 409
    return res

def test(request):
    print(request.method)
    res = HttpResponse('123')
    res.__setitem__('Access-Control-Allow-Origin', '*')

    return res

def facilities(request):
    if auth_func(request):
        body = {
        "username": auth_func(request)['uid'],
        "isAdding": False,
        "facilities": [],
        "showDeleteAlert": False,
        "showLogoutAlert": False,
        "isLoggedOut": False,
        "showAlert": False,
        "alertTitle": '',
        "isEditing": False,
        "facility": {"stripe": {"test": {}, "live": {}}}
        }
        res_body = json.dumps(body)
        res = HttpResponse(res_body)
        return res
    else:
        body = {
            "isAdding": False,
            "facilities": [],
            "showDeleteAlert": False,
            "showLogoutAlert": False,
            "isLoggedOut": True,
            "showAlert": False,
            "alertTitle": '',
            "isEditing": False,
            "facility": {"stripe": {"test": {}, "live": {}}}
        }
        res_body = json.dumps(body)
        res = HttpResponse(res_body)
        res.status_code = 401
        return res
'''




























