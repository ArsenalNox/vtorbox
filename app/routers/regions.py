"""
Эндпоинты регионов 

Создание, редактирование, импорт/экспорт 
"""

import os, uuid, re
import json

from typing import Annotated
from fastapi import APIRouter, Security, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from datetime import datetime
from shapely.geometry import shape, GeometryCollection, Point

from app.models import (
    Users, Session, engine, UsersAddress, 
    Address, IntervalStatuses, Roles, Permissions,
    Regions
    )

from app.auth import (
    oauth2_scheme, 
    get_current_user
)

from app import Tags


from app.validators import (
    UserLogin as UserLoginSchema,
    RegionOut
)


router = APIRouter()


@router.get('/regions', tags=[Tags.regions])
async def get_all_regions(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)],
    only_active: bool = True,
    search_query: str = None,
):
    """
    Получить список доступных регионов для сбора
    - **only_active**: вернуть только регионы, в которых проводится вывоз
    - **search_query**: поиск конкретного региона по названию, может быть как текстовый так и 
    формата "lat,long" для поиска региона, содержащего точку
    """
    
    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Regions)

        search_type = None
        if not search_query == None:
            if re.match(r'\d[\d]\.[\d]*,\d[\d]\.[\d]*', search_query):
                search_type = 1
            else:
                search_type = 2

            if search_type == 2:
                print(f'applying filter {search_query}')
                query = query.filter(Regions.name_full.ilike(f"%{search_query}%"))

        query = query.all()
        return_data = []
        for region in query:
            if search_type == 1:
                data_points = str(region.geodata).replace('\'','\"')
                data_points = json.loads(data_points)
                feature = shape(data_points)

                point = Point(float(search_query.split(',')[0]), float(search_query.split(',')[1]))
                if not feature.contains(point):
                    continue
                
            return_data.append(RegionOut(**region.__dict__))

        return return_data


@router.post('/regions', tags=[Tags.admins, Tags.regions])
async def import_regions_from_geojson(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=['admin'])],
    file: UploadFile,
    region_type: str = 'district'
    ):
    plain_regions = json.load(file.file)
    
    with Session(engine, expire_on_commit=False) as session:

        for feature in plain_regions['features']:
            if feature['properties']["name:ru"] == None:
                continue

            reg_query = session.query(Regions).filter_by(name_full = feature['properties']['name:ru']).first()
            if reg_query:
                continue

            print(feature['properties']["name:ru"])
            region_type = 'district'

            match feature['properties']['admin_level']:
                case 5:
                    region_type = 'district'

                case _:
                    pass
            
            new_region = Regions(
                name_full = feature['properties']['name:ru'],
                geodata = json.dumps(feature['geometry']),
                region_type = region_type
            )

            session.add(new_region)

        session.commit()