from datetime import datetime

from flask import render_template

from app import application, config, model


def get_month_stamp(date=None) -> str:
    """
    Generating month stamp (yyyy.m) 4 db
    :param date: datetime object or list of int, or timestamp
    :return: Month stamp 4 db
    """
    if type(date) is list:
        date = datetime(*date, 1)
    elif type(date) is int:
        date = datetime.fromtimestamp(date)
    else:
        date = datetime.today()
    date = date.timetuple()
    return f"{date.tm_year}.{date.tm_mon}"


def get_month_stat(date=None) -> dict:
    """
    Getting current month stat 4 header render
    :return: current month stat dict
    """
    stamp = date if type(date) is str else get_month_stamp(date)
    month_object = model.CustomPeriods.query.get(stamp)
    limit = month_object.limit if month_object else config["default_limit"]
    spending = sum(
        spending.amount for spending in model.Spending.query.filter_by(month=stamp)
    )
    return {"limit": limit, "spending": spending}


@application.context_processor
def inject_current_status():
    return {"current_status": get_month_stat()}
