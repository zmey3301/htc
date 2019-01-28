from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, FloatField, BooleanField
from wtforms.validators import DataRequired, Regexp
from app.model import Categories
from app import config
from datetime import datetime


class AddCategory(FlaskForm):
    name = StringField("Название категории:", validators=[DataRequired(message="Введите название категории")])


class AddSpending(FlaskForm):
    category = SelectField("Категория:",
                           default=0,
                           coerce=int,
                           choices=[(0, "Выберите категорию")] + [(category.id, category.name)
                                                                  for category
                                                                  in Categories.query.order_by("name").all()],
                           validators=[DataRequired(message="Выберите категорию")])
    date = DateField("Дата:",
                     default=datetime.today(),
                     validators=[DataRequired(message="Выберите дату")])
    amount = FloatField("Сумма:", validators=[DataRequired(message="Введите сумму")])


class UpdateLimit(FlaskForm):
    new_limit = FloatField("Новый лимит:", validators=[DataRequired(message="Введите лимит")])


class Settings(FlaskForm):
    default_limit = FloatField("Лимит по умолчанию:",
                               validators=[DataRequired(message="Введите новый лимит")],
                               default=config["default_limit"])
    adaptive_limit = BooleanField("Адаптивный лимит",
                                  default=config["adaptive_limit"],
                                  false_values=(False, 'false', 0, '0'))


class CustomLimit(FlaskForm):
    first_month = StringField("Начало периода:",
                              validators=[DataRequired(message="Введите начало периода"),
                                          Regexp("^\d{4}-[0-1]?\d$",
                                                 message="Введите дату в формате ГГГГ-ММ")])
    last_month = StringField("Конец периода (не обязательно):",
                             validators=[Regexp("^(?:\d{4}-[0-1]?\d|[\s]*)$",
                                                message="Введите дату в формате ГГГГ-ММ")])
    limit = FloatField("Лимит:", validators=[DataRequired(message="Введите лимит")])
