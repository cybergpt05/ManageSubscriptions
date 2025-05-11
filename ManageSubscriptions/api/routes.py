from flask import Blueprint
from flask import request,jsonify
from ManageSubscriptions import db
from ManageSubscriptions.models import Client,ClientPlan,ClientSubscriber,APIUsageTrack
from datetime import datetime,timedelta
from .helpers import is_valid_date
api_bp = Blueprint('api',__name__)

@api_bp.route('/api/subscribers', methods=["GET"])
def api_subscribers():
    api_token = request.headers.get('X-API-KEY')
    if not api_token:
        return jsonify({"message":"API token is missing.","status":400}),400
    client = Client.query.filter_by(api_token=api_token).first()
    if client is None:
        return jsonify({"message":"Ivalid API token.","status":400}),400
    try:
        client.requests+=1
        api_log = APIUsageTrack.query.filter_by(client_id=client.id,usage_date=datetime.now().date()).first()
        if api_log:
            api_log.usage_quantity+=1
        else:
            api_log = APIUsageTrack(client_id=client.id,usage_date=datetime.now().date(),usage_quantity=1)
            db.session.add(api_log)
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({"message":"Request was not processed.","status":400}),400
    requests = client.requests
    allowed_requests = client.allowed_requests
    if allowed_requests - requests <= 0:
        return jsonify({"message":"You exceeded your limit, upgrade your plan to access API.","status":400}),400
    client_subscribers = client.subscribers
    subscribers = {}
    subscriber_counter = 1
    if client_subscribers:
        for subscriber in client_subscribers:
            plan = ClientPlan.query.filter_by(id=subscriber.plan_id).first()
            if plan:
                plan_name = plan.name
            else:
                plan_name = None
            subscribers[subscriber_counter] = {"subscriber_id":subscriber.user_id,"subscriber_plan":plan_name,"start_date":subscriber.start_date,"end_date":subscriber.end_date,"remaining_days":subscriber.remaining_days,"is_active":subscriber.active,"meta_data":subscriber.meta_data,"created_at":subscriber.created_at}
            subscriber_counter+=1
        return jsonify(subscribers), 200
    else:
        return jsonify({"message":"You have no subscribers.","status":200}), 200

@api_bp.route('/api/subscriber/<id>', methods=["GET","DELETE","PATCH"])
def api_subscriber(id):
    api_token = request.headers.get('X-API-KEY')
    if not api_token:
        return jsonify({"message":"API token is missing.","status":400}),400
    client = Client.query.filter_by(api_token=api_token).first()
    if client is None:
        return jsonify({"message":"Ivalid API token.","status":400}),400
    client.requests+=1
    try:
        api_log = APIUsageTrack.query.filter_by(client_id=client.id,usage_date=datetime.now().date()).first()
        if api_log:
            api_log.usage_quantity+=1
        else:
            api_log = APIUsageTrack(client_id=client.id,usage_date=datetime.now().date(),usage_quantity=1)
            db.session.add(api_log)
    except:
        pass
        return jsonify({"message":"Request was not processed.","status":400}),400
    requests = client.requests
    allowed_requests = client.allowed_requests
    if allowed_requests - requests <= 0:
        return jsonify({"message":"You exceeded your limit, upgrade your plan to access API.","status":400}),400
    if request.method == "GET":
        subscriber_info = ClientSubscriber.query.filter_by(user_id=id,client_id=client.id).first()
        if subscriber_info:
            user_id = subscriber_info.user_id
            plan_id = ClientPlan.query.filter_by(id=subscriber_info.plan_id).first()
            if plan_id:
                plan_id = plan_id.name
            else:
                plan_id= None
            start_date = subscriber_info.start_date
            end_date = subscriber_info.end_date
            active = subscriber_info.active
            meta_data = subscriber_info.meta_data
            created_at = subscriber_info.created_at
            remaining_days = subscriber_info.remaining_days
            subscriber_info = {"subscriber_id":user_id,"subscriber_plan":plan_id,"start_date":start_date,"end_date":end_date,"remaining_days":remaining_days,"is_active":active,"meta_data":meta_data,"created_at":created_at}
            return jsonify(subscriber_info), 200
        return jsonify({"message":"There is no subscriber associated with this id","status":400}), 400
    if request.method == "PATCH":
        subscriber = ClientSubscriber.query.filter_by(user_id=id,client_id=client.id).first()
        if subscriber:
            if not request.is_json:
                return jsonify({"message":"Invalid or missing JSON data.","status":400}), 400
            data = request.get_json(silent=True)
            if data is None:
                return jsonify({"message": "Empty or malformed JSON.","status":400}), 400
            data_to_patch = {}
            valid_data = ['user_id','plan_name','start_date','end_date','remaining_days','active','meta_data','renew']
            for vdata in valid_data:
                try:
                    if data[vdata] == None:
                        if vdata != "meta_data":
                            return jsonify({"message":f"{vdata} can't be null.","status":400}), 400
                    data_to_patch[vdata] = data[vdata]
                except:
                    pass
            try:
                is_active = vdata['active']
                if not isinstance(is_active,bool):
                    return jsonify({"message":"active value should be boolean.","status":400}), 400
            except:
                pass
            try:
                data_to_patch['remaining_days'] = int(data_to_patch['remaining_days'])
            except KeyError:
                pass
            except:
                return jsonify({"message":f"remaining_days should be an integer.","status":400}), 400
            try:
                name =data_to_patch['plan_name']
                plan_id = ClientPlan.query.filter_by(name=name, client_id=client.id).first()
                if plan_id:
                    del data_to_patch['plan_name']
                    data_to_patch['plan_id'] = plan_id.id
                else:
                    return jsonify({"message":f"You have no plan called {name}.","status":400}), 400
            except:
                pass
            try:
                start = data_to_patch['start_date']
                if not is_valid_date(start):
                    return jsonify({"message":"Date must be in YYYY-MM-DD format.","status":400}), 400
                data_to_patch['start_date'] = datetime.strptime(start, "%Y-%m-%d").date()
            except:
                pass
            try:
                end = data_to_patch['end_date']
                if not is_valid_date(end):
                    return jsonify({"message":"Date must be in YYYY-MM-DD format.","status":400}), 400
                data_to_patch['end_date'] = datetime.strptime(end, "%Y-%m-%d").date()
            except:
                pass
            try:
                if data_to_patch['active'] == False:
                    data_to_patch['remaining_days'] = 0
            except:
                pass
            if subscriber.active == False:
                data_to_patch['remaining_days'] = 0
            if data_to_patch:
                for key,value in data_to_patch.items():
                    setattr(subscriber, key, value)
                db.session.commit()
                return jsonify({"message":"Data updated successfully.","status":200}), 200
            else:
                return jsonify({"message":"No data was sent to patch.","status":400}), 400
        else:
            return jsonify({"message":"There is no subscriber associated with this id","status":400}), 400
    if request.method == "DELETE":
        subscriber_to_delete = ClientSubscriber.query.filter_by(client_id=client.id, user_id=id).first()
        if subscriber_to_delete:
            try:
                db.session.delete(subscriber_to_delete)
                db.session.commit()
                return jsonify({"message":"Subscriber is deleted successfully.","status":200}), 200
            except:
                db.session.rolback()
                return jsonify({"message":"Failed to delete subscriber.","status":400}), 400
        return jsonify({"message":"There is no subscriber associated with this id","status":400}), 400

@api_bp.route('/api/subscriber/<string:id>/renew', methods=["GET"])
def subscriber_renew(id):
    api_token = request.headers.get('X-API-KEY')
    if not api_token:
        return jsonify({"message":"API token is missing.","status":400}),400
    client = Client.query.filter_by(api_token=api_token).first()
    if client is None:
        return jsonify({"message":"Ivalid API token.","status":400}),400
    client.requests+=1
    try:
        api_log = APIUsageTrack.query.filter_by(client_id=client.id,usage_date=datetime.now().date()).first()
        if api_log:
            api_log.usage_quantity+=1
        else:
            api_log = APIUsageTrack(client_id=client.id,usage_date=datetime.now().date(),usage_quantity=1)
            db.session.add(api_log)
    except:
        pass
        return jsonify({"message":"Request was not processed.","status":400}),400
    requests = client.requests
    allowed_requests = client.allowed_requests
    if allowed_requests - requests <= 0:
        return jsonify({"message":"You exceeded your limit, upgrade your plan to access API.","status":400}),400
    subscriber = ClientSubscriber.query.filter_by(client_id=client.id, user_id=id).first()
    if subscriber:
        subscriber.active = True
        subscriber.start_date = datetime.now().date()
        duration_days = ClientPlan.query.filter_by(id=subscriber.plan_id).first().duration_days
        subscriber.end_date = datetime.now().date() + timedelta(days=duration_days)
        subscriber.remaining_days = duration_days
        db.session.commit()
        return jsonify({"message":"subscription renewed successfully.","status":200}), 200
    return jsonify({"message":"There is no subscriber associated with this id","status":400}), 400


@api_bp.route('/api/subscriber', methods=["POST"])
def api_add_subscriber():
    api_token = request.headers.get('X-API-KEY')
    if not api_token:
        return jsonify({"message":"API token is missing.","status":400}),400
    client = Client.query.filter_by(api_token=api_token).first()
    if client is None:
        return jsonify({"message":"Ivalid API token.","status":400}),400
    try:
        client.requests+=1
        api_log = APIUsageTrack.query.filter_by(client_id=client.id,usage_date=datetime.now().date()).first()
        if api_log:
            api_log.usage_quantity+=1
        else:
            api_log = APIUsageTrack(client_id=client.id,usage_date=datetime.now().date(),usage_quantity=1)
            db.session.add(api_log)
    except:
        pass
        return jsonify({"message":"Request was not processed.","status":400}),400
    requests = client.requests
    allowed_requests = client.allowed_requests
    if allowed_requests - requests <= 0:
        return jsonify({"message":"You exceeded your limit, upgrade your plan to access API.","status":400}),400
    if len(client.subscribers) >= client.subscribers_limit:
        return jsonify({"message":"You exceeded your number of subscribers limit, upgrade your plan to add more subscribers.","status":400}),400
    if request.method == "POST":
        if not request.is_json:
            return jsonify({"message":"Invalid or missing JSON data.","status":400}), 400
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"message": "Empty or malformed JSON.","status":400}), 400
        required_data = ['user_id','plan_name','active']
        not_required_data = ["meta_data",'start_date','end_date']
        plan_duration_days = 0
        data_to_post = {}
        for required_value in required_data:
            try:
                if data[required_value] != None:
                    data_to_post[required_value] = data[required_value]
                else:
                    return jsonify({"message":f"{required_value} can't be null.","status":400}), 400
            except:
                return jsonify({"message":f"{required_value} is missing.","status":400}), 400
        for not_required_value in not_required_data:
            try:
                data_to_post[not_required_value] = data[not_required_value]
            except:
                pass
        try:
            is_active = data['active']
            if not isinstance(is_active,bool):
                return jsonify({"message":"active value should be boolean.","status":400}), 400
        except:
            pass
        try:
            name =data_to_post['plan_name']
            plan_id = ClientPlan.query.filter_by(name=name, client_id=client.id).first()
            if plan_id:
                plan_duration_days = plan_id.duration_days
                del data_to_post['plan_name']
                data_to_post['plan_id'] = plan_id.id
            else:
                return jsonify({"message":f"You have no plan called {name}.","status":400}), 400
        except:
            pass
        try:
            start = data_to_post['start_date']
            if not is_valid_date(start):
                return jsonify({"message":"Date must be in YYYY-MM-DD format.","status":400}), 400
            data_to_post['start_date'] = datetime.strptime(start, "%Y-%m-%d").date()
        except:
            pass
        try:
            end = data_to_post['end_date']
            if not is_valid_date(end):
                return jsonify({"message":"Date must be in YYYY-MM-DD format.","status":400}), 400
            data_to_post['end_date'] = datetime.strptime(end, "%Y-%m-%d").date()
        except:
            pass
        is_subscriber_exists = ClientSubscriber.query.filter_by(user_id=data_to_post['user_id'], client_id=client.id).first()
        if is_subscriber_exists:
            return jsonify({"message":"Subscriber with this id already exists","status":400}), 400
        try:
            meta_data = data_to_post['meta_data']
        except KeyError:
            data_to_post['meta_data'] = None
        try:
            end_date = data_to_post['end_date']
            if end_date:
                try:
                    start_date = data_to_post['start_date']
                except KeyError:
                    return jsonify({"message":"specify a start_date before specifying an end_date.","status":400}), 400
        except:
            pass
        try:
            start_date = data_to_post['start_date']
            if start_date:
                try:
                    end_date = data_to_post['end_date']
                    data_to_post['remaining_days'] = int(str(end_date - start_date).split()[0])
                except KeyError:
                    data_to_post['end_date'] = start_date + timedelta(days=plan_duration_days)
                    data_to_post['remaining_days'] = int(str(data_to_post['end_date'] - start_date).split()[0])
        except KeyError:
            data_to_post['start_date'] = datetime.now().date()
            data_to_post['end_date'] = datetime.now().date() + timedelta(days=plan_duration_days)
            data_to_post['remaining_days'] = plan_duration_days
        if data_to_post['active'] == False:
            data_to_post['remaining_days'] = 0
        subscriber = ClientSubscriber(client_id=client.id,user_id=data_to_post['user_id'],plan_id=data_to_post['plan_id'],start_date=data_to_post['start_date'],end_date=data_to_post['end_date'],active=data_to_post['active'],remaining_days=data_to_post['remaining_days'],meta_data=data_to_post['meta_data'])
        db.session.add(subscriber)
        db.session.commit()
        return jsonify({"message":"Subscriber is added successfully.","status":200}), 200

@api_bp.route('/api/plans', methods=["GET"])
def api_plans():
    api_token = request.headers.get('X-API-KEY')
    if not api_token:
        return jsonify({"message":"API token is missing.","status":400}),400
    client = Client.query.filter_by(api_token=api_token).first()
    if client is None:
        return jsonify({"message":"Ivalid API token.","status":400}),400
    try:
        client.requests+=1
        api_log = APIUsageTrack.query.filter_by(client_id=client.id,usage_date=datetime.now().date()).first()
        if api_log:
            api_log.usage_quantity+=1
        else:
            api_log = APIUsageTrack(client_id=client.id,usage_date=datetime.now().date(),usage_quantity=1)
            db.session.add(api_log)
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({"message":"Request was not processed.","status":400}),400
    requests = client.requests
    allowed_requests = client.allowed_requests
    if allowed_requests - requests <= 0:
        return jsonify({"message":"You exceeded your limit, upgrade your plan to access API.","status":400}),400
    client_plans = client.plans
    plans = {}
    plan_counter = 1
    if client_plans:
        for plan in client_plans:
            plans[plan_counter] = {"name":plan.name,"duration_days":plan.duration_days,"description":plan.description}
            plan_counter+=1
        return jsonify(plans), 200
    else:
        return jsonify({"message":"You have no plans.","status":200}), 200
    
@api_bp.route('/api/plan', methods=["POST"])
def api_add_plan():
    api_token = request.headers.get('X-API-KEY')
    if not api_token:
        return jsonify({"message":"API token is missing.","status":400}),400
    client = Client.query.filter_by(api_token=api_token).first()
    if client is None:
        return jsonify({"message":"Ivalid API token.","status":400}),400
    try:
        client.requests+=1
        api_log = APIUsageTrack.query.filter_by(client_id=client.id,usage_date=datetime.now().date()).first()
        if api_log:
            api_log.usage_quantity+=1
        else:
            api_log = APIUsageTrack(client_id=client.id,usage_date=datetime.now().date(),usage_quantity=1)
            db.session.add(api_log)
    except:
        pass
        return jsonify({"message":"Request was not processed.","status":400}),400
    requests = client.requests
    allowed_requests = client.allowed_requests
    if allowed_requests - requests <= 0:
        return jsonify({"message":"You exceeded your limit, upgrade your plan to access API.","status":400}),400
    if len(client.plans) >= client.plans_limit:
        return jsonify({"message":"You exceeded your number of plans limit, upgrade your plan to add more plans.","status":400}),400
    if request.method == "POST":
        if not request.is_json:
            return jsonify({"message":"Invalid or missing JSON data.","status":400}), 400
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"message": "Empty or malformed JSON.","status":400}), 400
        required_data = ['name','duration_days']
        not_required_data = ['description']
        data_to_post = {}
        for required_value in required_data:
            try:
                if data[required_value] != None:
                    data_to_post[required_value] = data[required_value]
                else:
                    return jsonify({"message":f"{required_value} can't be null.","status":400}), 400
            except:
                return jsonify({"message":f"{required_value} is missing.","status":400}), 400
        for not_required_value in not_required_data:
            try:
                data_to_post[not_required_value] = data[not_required_value]
            except:
                pass
        try:
            data_to_post['duration_days'] = int(data_to_post['duration_days'])
            if (data_to_post['duration_days'] > 3650):
                return jsonify({"message":"duration days limit is 3650 day.","status":400}), 400 
        except:
            return jsonify({"message":"duration days should be an integer.","status":400}), 400 
        is_plan_exists = ClientPlan.query.filter_by(client_id=client.id,name=data_to_post['name']).first()
        if is_plan_exists:
            return jsonify({"message":"Plan already exists","status":400}), 400
        try:
            description = data_to_post['description']
            plan = ClientPlan(client_id=client.id,name=data_to_post['name'],duration_days=data_to_post['duration_days'],description=description)
        except:
            plan = ClientPlan(client_id=client.id,name=data_to_post['name'],duration_days=data_to_post['duration_days'])
        db.session.add(plan)
        db.session.commit()
        return jsonify({"message":"Plan is added successfully.","status":200}), 200

@api_bp.route('/api/plan/<name>', methods=["GET","DELETE","PATCH"])
def api_plan(name):
    api_token = request.headers.get('X-API-KEY')
    if not api_token:
        return jsonify({"message":"API token is missing.","status":400}),400
    client = Client.query.filter_by(api_token=api_token).first()
    if client is None:
        return jsonify({"message":"Ivalid API token.","status":400}),400
    client.requests+=1
    try:
        api_log = APIUsageTrack.query.filter_by(client_id=client.id,usage_date=datetime.now().date()).first()
        if api_log:
            api_log.usage_quantity+=1
        else:
            api_log = APIUsageTrack(client_id=client.id,usage_date=datetime.now().date(),usage_quantity=1)
            db.session.add(api_log)
    except:
        pass
        return jsonify({"message":"Request was not processed.","status":400}),400
    requests = client.requests
    allowed_requests = client.allowed_requests
    if allowed_requests - requests <= 0:
        return jsonify({"message":"You exceeded your limit, upgrade your plan to access API.","status":400}),400
    if request.method == "GET":
        plan_info = ClientPlan.query.filter_by(name=name,client_id=client.id).first()
        if plan_info:
            name = plan_info.name
            duration_days = plan_info.duration_days
            description = plan_info.description
            plan_info = {"name":name,"duration_days":duration_days,"description":description}
            return jsonify(plan_info), 200
        return jsonify({"message":"You have no plan associated with this name.","status":400}), 400
    if request.method == "PATCH":
        plan = ClientPlan.query.filter_by(name=name,client_id=client.id).first()
        if plan:
            if not request.is_json:
                return jsonify({"message":"Invalid or missing JSON data.","status":400}), 400
            data = request.get_json(silent=True)
            if data is None:
                return jsonify({"message": "Empty or malformed JSON.","status":400}), 400
            data_to_patch = {}
            valid_data = ['name','duration_days','description']
            for vdata in valid_data:
                try:
                    data_to_patch[vdata] = data[vdata]
                except:
                    pass
            try:
                planname =data_to_patch['name']
                if not planname:
                    return jsonify({"message":f"name can't be null.","status":400}), 400
                plan_id = ClientPlan.query.filter_by(name=planname, client_id=client.id).first()
                if plan_id and (name != planname) :
                    return jsonify({"message":f"You already have a plan called {planname}.","status":400}), 400
            except:
                pass
            try:
                data_to_patch['duration_days'] = int(data_to_patch['duration_days'])
                if (data_to_patch['duration_days'] > 3650):
                    return jsonify({"message":"duration days limit is 3650 day.","status":400}), 400 
            except KeyError:
                pass
            except:
                return jsonify({"message":"duration days should be an integer.","status":400}), 400
            if data_to_patch:
                for key,value in data_to_patch.items():
                    setattr(plan, key, value)
                db.session.commit()
                return jsonify({"message":"Data updated successfully.","status":200}), 200
            else:
                return jsonify({"message":"No data was sent to patch.","status":400}), 400
        else:
            return jsonify({"message":"You have no plan associated with this name.","status":400}), 400
    if request.method == "DELETE":
        plan = ClientPlan.query.filter_by(name=name,client_id=client.id).first()
        if plan:
            try:
                db.session.delete(plan)
                db.session.commit()
                return jsonify({"message":"Plan is deleted successfully.","status":200}), 200
            except:
                db.session.rolback()
                return jsonify({"message":"Failed to delete plan.","status":400}), 400
        return jsonify({"message":"You have no plan associated with this name.","status":400}), 400