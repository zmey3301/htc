from app import application, db, config
from app.model import Categories, Spending, CustomPeriods
from app.forms import AddCategory, AddSpending, UpdateLimit, Settings, CustomLimit
from app.helpers import render, get_month_stamp
from flask import request, flash, abort, redirect
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from calendar import Calendar
import json
import re
month_stamp_regex = "^\d{4}\.(?:1[0-2]|[0-9])$"


@application.route("/")
@application.route("/index")
def index():
    def get_limit(month):
        month_data = CustomPeriods.query.get(month)
        return month_data.limit if month_data else config["default_limit"]
    data = Spending.query.all()
    groups = {spending.month for spending in data}
    grouped_data = sorted(
        tuple(
            {
                "month": month,
                "amount": sum(spending.amount for spending in data if spending.month == month),
                "limit": get_limit(month)
            } for month in groups),
        key=lambda x: x["month"])
    return render("/index.html", title="Главная", data=grouped_data)


@application.route("/month-detail/<string:month_stamp>")
def month_detail(month_stamp):
    if not re.match(month_stamp_regex, month_stamp):
        return abort(404)
    else:
        categories = Categories.query.order_by(Categories.name).all()
        year, month = (int(item) for item in month_stamp.split("."))
        table = tuple(
            tuple(
                sum(
                    spending.amount
                    for spending in category.spending.filter_by(date=datetime(year, month, day)).all()
                )
                for category in categories
            )
            for day in Calendar().itermonthdays(year, month) if day
        )
        month_data = CustomPeriods.query.get(month_stamp)
        month_limit = month_data.limit if month_data else config["default_limit"]
        month_amount = sum(spending.amount for spending in Spending.query.filter_by(month=month_stamp).all())
        return render("/month-detail.html", title=f"Отчет за месяц {month_stamp}", month=month_stamp,
                      table=table, categories=categories, month_limit=month_limit, month_amount=month_amount)


@application.route("/add-category", methods=["GET", "POST"])
def add_category():
    form = AddCategory()
    if request.method == "POST" and form.validate_on_submit():
        if Categories.query.filter_by(name=form.name.data).one_or_none() is not None:
            flash("Данная категория уже существует")
        else:
            category = Categories(name=form.name.data)
            db.session.add(category)
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("Произошла ошибка")
            else:
                flash("Категория успешно добавлена")
    return render("/category-form.html", form=form, title="Добавление категории")


@application.route("/add-cost", methods=["GET", "POST"])
def add_cost():
    form = AddSpending()
    if request.method == "POST" and form.validate_on_submit():
        month_stamp = get_month_stamp(form.date.data)
        spending = Spending(category_id=form.category.data, amount=round(form.amount.data, 2),
                            date=form.date.data, month=month_stamp)
        db.session.add(spending)
        try:
            db.session.commit()
        except SQLAlchemyError:
            flash("Произошла ошибка")
        else:
            flash("Расход учтен успешно")
            current_month_amount = sum(spending.amount for spending in Spending.query.filter_by(month=month_stamp))
            month_data = CustomPeriods.query.get(month_stamp)
            current_month_limit = month_data.limit if month_data else config["default_limit"]
            if current_month_amount > current_month_limit:
                if config["adaptive_limit"]:
                    overflow = current_month_amount - current_month_limit
                    year, month = (int(element) for element in month_stamp.split("."))
                    if month == 12:
                        year += 1
                        month = 1
                    else:
                        month += 1
                    new_month_stamp = get_month_stamp([year, month])
                    new_month = CustomPeriods.query.get(new_month_stamp)
                    if new_month:
                        new_month.limit -= overflow
                    else:
                        new_month = CustomPeriods(id=new_month_stamp, limit=config["default_limit"] - overflow)
                        db.session.add(new_month)
                    try:
                        db.session.commit()
                    except SQLAlchemyError:
                        db.session.rollback()
                        flash("При изменений предела следующего месяца произошла ошибка")
                else:
                    return redirect(f"/update-limit/{month_stamp}")
    return render("/cost-form.html", form=form, title="Добавление расхода")


@application.route("/update-limit/<string:month>", methods=["GET", "POST"])
def update_limit(month):
    if not re.match(month_stamp_regex, month):
        return abort(404)
    form = UpdateLimit()
    month_data = CustomPeriods.query.get(month)
    month_amount = sum(spending.amount for spending in Spending.query.filter_by(month=month).all())
    if request.method == "POST" and form.validate_on_submit():
        new_limit = round(form.new_limit.data, 2)
        if new_limit < month_amount:
            error_message = "Лимит должен превышать затраты выбранного месяца"
            form.errors["new_limit"] = [error_message]
        else:
            if month_data:
                month_data.limit = new_limit
            else:
                new_month_data = CustomPeriods(id=month, limit=new_limit)
                db.session.add(new_month_data)
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("При обновлении данных произошла ошибка")
            else:
                flash("Данные успешно обновлены")
                return redirect("/add-cost")
    month_limit = month_data.limit if month_data else config["default_limit"]
    return render("/limit-update-form.html", title="Обновление месячных лимитов", form=form,
                  month_limit=month_limit, month_amount=month_amount)


@application.route("/settings", methods=["GET", "POST"])
def settings():
    def update_month(stamp_data, limit):
        stamp = get_month_stamp(stamp_data)
        data = CustomPeriods.query.get(stamp)
        if data:
            data.limit = limit
        else:
            new_data = CustomPeriods(id=stamp, limit=limit)
            db.session.add(new_data)
    settings_form = Settings()
    limit_form = CustomLimit()
    # Проверяем default_limit т.к. is_submitting сломало
    if request.method == "POST" and request.form.get("default_limit") and settings_form.validate_on_submit():
        config["default_limit"] = round(settings_form.default_limit.data, 2)
        config["adaptive_limit"] = settings_form.adaptive_limit.data
        with open("app.json", "w") as config_file:
            config_file.write(json.dumps(config))
        flash("Конфигурация успешно обновлена!")
    elif request.method == "POST" and request.form.get("limit") and limit_form.validate_on_submit():
        year, month = (int(item) for item in limit_form.first_month.data.split("-"))
        new_limit = round(limit_form.limit.data, 2)
        if limit_form.last_month.data.strip():
            last_year, last_month = (int(item) for item in limit_form.last_month.data.split("-"))
            if year == last_year and month >= last_month or year > last_year:
                limit_form.errors["last_month"] = ["Вторая дата должна быть больше первой"]
            else:
                while year <= last_year or month <= last_month:
                    update_month([year, month], new_limit)
                    if month == 12:
                        year += 1
                        month = 1
                    else:
                        month += 1
                try:
                    db.session.commit()
                except SQLAlchemyError:
                    db.session.rollback()
                    flash("Во время обновления лимитов произошла ошибка")
                else:
                    flash("Лимиты успешно обновлены")
        else:
            update_month([year, month], new_limit)
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("Во время обновления лимита произошла ошибка")
            else:
                flash("Лимит успешно обновлен")
    return render("/settings.html", title="Настройки", settings_form=settings_form, limit_form=limit_form)
