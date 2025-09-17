from flask import redirect, render_template, session
from functools import wraps

dormitory_names = [
    "Dormitory 1",
    "Dormitory 2",
    "Dormitory 3",
    "Dormitory 4",
    "Dormitory 5",
    "Dormitory 6",
    "Dormitory 7",
    "Dormitory 8",
    "Dormitory 9",
    "Dormitory 19",
    "İsa Demiray Dormitory",
    "Faika Demiray Dormitory",
    "Refika Aksoy Dormitory",
    "Faik Hiziroğlu Guest House",
    "Osman Yazici Guest House",
    "12. Guest House",
    "15. Guest House",
    "16. Guest House",
]
dormitories = [
    {"name": "Dormitory 1", "gender": "female", "occupancy": "double"},
    {"name": "Dormitory 2", "gender": "male", "occupancy": "double"},
    {"name": "Dormitory 3", "gender": "female", "occupancy": "quadruple"},
    {"name": "Dormitory 4", "gender": "male", "occupancy": "quadruple"},
    {"name": "Dormitory 5", "gender": "female", "occupancy": "quadruple"},
    {"name": "Dormitory 6", "gender": "male", "occupancy": "quadruple"},
    {"name": "Dormitory 7", "gender": "female", "occupancy": "quadruple"},
    {"name": "Dormitory 8", "gender": "male", "occupancy": "double"},
    {"name": "Dormitory 9", "gender": "male", "occupancy": "double"},
    {"name": "Dormitory 19", "gender": "mixed", "occupancy": "double"},
    {"name": "İsa Demiray Dormitory", "gender": "male", "occupancy": "quadruple"},
    {"name": "Faika Demiray Dormitory", "gender": "female", "occupancy": "quadruple"},
    {"name": "Refika Aksoy Dormitory", "gender": "mixed", "occupancy": "quadruple"},

    # Guest Houses
    {"name": "Faik Hiziroğlu Guest House", "gender": "male", "occupancy": "single/double/triple/quadruple"},
    {"name": "Osman Yazici Guest House", "gender": "female", "occupancy": "single/double/triple/quadruple"},
    {"name": "12. Guest House", "gender": "female", "occupancy": "single/double/triple/quadruple"},
    {"name": "15. Guest House", "gender": "male", "occupancy": "single/double/triple/quadruple"},
    {"name": "16. Guest House", "gender": "female", "occupancy": "single/double/triple/quadruple"},
]
laundry_time_intervals = {
    1: "08:00-10:00",
    2: "10:00-12:00",
    3: "12:00-14:00",
    4: "14:00-16:00",
    5: "16:00-18:00",
    6: "18:00-20:00",
    7: "20:00-22:00",
    8: "22:00-00:00"
}
def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function
