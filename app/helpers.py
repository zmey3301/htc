from app import model, config
from datetime import datetime
from flask import render_template


def get_month_stamp(date=None):
    """
    Generating month stamp (yyyy.m) 4 db
    :param date: datetime object or list of int, or timestamp
    :return: Month stamp 4 db
    """
    if type(date) is list:
        date = datetime(*date, 1)
    elif type(date) is int:
        date = datetime.fromtimestamp(date)
    elif date is None:
        date = datetime.today()
    date = date.timetuple()
    return f"{date.tm_year}.{date.tm_mon}"


def get_month_stat():
    """
    Getting current month stat 4 header render
    :return: current month stat dict
    """
    today = datetime.today().timetuple()
    stamp = f"{today.tm_year}.{today.tm_mon}"
    month_object = model.CustomPeriods.query.get(stamp)
    limit = month_object.limit if month_object else config["default_limit"]
    spending = sum(spending.amount for spending in model.Spending.query.filter_by(month=stamp))
    return {
        "limit": limit,
        "spending": spending
    }


def render(template, **kwargs):
    """
    render_template proxy 4 default vars adding
    :param template: Jinja2 template path
    :param kwargs: Jinja2 template params
    :return: Rendered template
    """
    return render_template(template, current_status=get_month_stat(), **kwargs)
