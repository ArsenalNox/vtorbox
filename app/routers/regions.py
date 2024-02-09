"""
Эндпоинты регионов 

Создание, редактирование, импорт/экспорт 
"""

import os, re
import json

from typing import Annotated
from fastapi import APIRouter, Security, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from datetime import datetime
from shapely.geometry import shape, GeometryCollection, Point
from uuid import UUID

from app.models import (
    Users, Session, engine, UsersAddress, 
    Address, IntervalStatuses, Roles, Permissions,
    Regions, WEEK_DAYS_WORK_STR_LIST
    )

from app.auth import (
    oauth2_scheme, 
    get_current_user
)

from app import Tags


from app.validators import (
    UserLogin as UserLoginSchema,
    RegionOut, RegionUpdate
)


router = APIRouter()

#TODO: Добавить привязку к рабочим дням недели
@router.get('/regions', tags=[Tags.regions])
async def get_all_regions(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)],
    only_active: bool = True,
    with_work_days: bool = False,

    search_query: str = None
):
    """
    Получить список доступных регионов для сбора
    - **only_active**: вернуть только регионы, в которых проводится вывоз
    - **search_query**: поиск конкретного региона по названию, может быть как текстовый так и 
    формата "lat,long" для поиска региона, содержащего точку
    - **with_work_days**: Отображать информацию о рабочих днях региона
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
                query = query.filter(Regions.name_full.ilike(f"%{search_query}%"))

        query = query.all()


        if search_type == 1:
            region = Regions.get_by_coords(float(search_query.split(',')[0]), float(search_query.split(',')[1]))
            region.work_days = str(region.work_days).split(' ')
            return RegionOut(**region.__dict__)

        return_data = []
        for region in query:
            region.work_days = str(region.work_days).split(' ')
            return_data.append(RegionOut(**region.__dict__))

        return return_data


@router.post('/regions', tags=[Tags.admins, Tags.regions])
async def import_regions_from_geojson(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=['admin'])],
    file: UploadFile,
    region_type: str = 'district',
    update_existing: bool = False
    ):
    """
    Импортировать рабочие районы из geojson файла
    - **file**: Файл с данными
    - **region_type**: Форс типа импортируемых районов, по умолчанию определяет 
    от admin_level в feature 
    - **update_existing**: Обновлять ли уже существующие районы, если они 
    найдены по названию
    """
    plain_regions = json.load(file.file)
    
    with Session(engine, expire_on_commit=False) as session:
        added_count = 0
        updated_count = 0
        invalid_data = []

        for feature in plain_regions['features']:
            if feature['properties']["name:ru"] == None:
                continue

            reg_query = session.query(Regions).filter_by(name_full = feature['properties']['name:ru']).first()

            print(feature['properties']["name:ru"])
            region_type = 'district'

            match feature['properties']['admin_level']:
                #TODO: Сделать кейсы под остальные admin_level's
                case 5:
                    region_type = 'district'

                case _:
                    pass
            
            if reg_query and (update_existing):
                reg_query.geodata = json.dumps(feature['geometry'])
                reg_query.region_type = region_type
                updated_count+=1
                session.add(reg_query)

            elif not reg_query:
                new_region = Regions(
                    name_full = feature['properties']['name:ru'],
                    geodata = json.dumps(feature['geometry']),
                    region_type = region_type
                )
                added_count+=1
                session.add(new_region)

            else:
                continue
        
        session.commit()

        return JSONResponse({
            "added_count": added_count,
            "updated_count": updated_count,
            "invalid": invalid_data,
        }, status_code=200)


@router.put('/regions/{region_id}', tags=[Tags.regions, Tags.managers])
async def update_region_data(
        new_data: RegionUpdate,
        region_id: UUID
    ) -> RegionOut:
    """
    Обновить данные региона 
    """
    print(new_data)

    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Regions).filter_by(id=region_id).first()
        if not query: 
            return JSONResponse({
                "message": "Not found"
            }, status_code=404)


        for attr, value in new_data.model_dump().items():
            if value == None:
                continue

            if attr == 'work_days' and not (value == None):
                print(value)
                for day in value:
                    if day not in WEEK_DAYS_WORK_STR_LIST:
                        return JSONResponse({
                            "message": "invalid weekday"
                        }, status_code=422)

                print('updating work days')
                query.work_days = ' '.join(value)

        session.commit()

        return_data = query.__dict__
        return_data['work_days'] = str(return_data['work_days']).split(' ')
        return return_data