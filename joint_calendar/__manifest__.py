# -*- coding: utf-8 -*-
{
    "name": "Joint Calendar",
    "version": "13.0.2.0.1",
    "category": "Extra Tools",
    "author": "faOtools",
    "website": "https://faotools.com/apps/13.0/joint-calendar-381",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "calendar",
        "mail"
    ],
    "data": [
        "security/security.xml",
        "views/configurations.xml",
        "views/event_rule_view.xml",
        "views/joint_calendar_view.xml",
        "views/joint_event_view.xml",
        "views/menu.xml",
        "data/cron.xml",
        "data/data.xml",
        "security/ir.model.access.csv"
    ],
    "qweb": [
        
    ],
    "js": [
        
    ],
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The tool to combine different Odoo events in a few configurable super calendars. Shared calendar. Common calendar.",
    "description": """
For the full details look at static/description/index.html

* Features * 
- Multifarious events on a single calendar
- Fast switching between functional areas
- Topical and relevant information
- Automatic reminders for any Odoo document
- Quick access to source details
- Simple user rights administration
- Used in any functional area

* Extra Notes *
- How to add a new document type for a joint calendar
- How to configure a new joint calendar based on rules
- How are source documents and joint events interrelated
- How to introduce a warning system
- More details about joint calendar security
- Have a look at typical use cases


#odootools_proprietary

    """,
    "images": [
        "static/description/main.png"
    ],
    "price": "65.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=27&ticket_version=13.0&url_type_id=3",
}