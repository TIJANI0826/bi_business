app_name = "bi_assisstant"
app_title = "Business Intelligence Assistant"
app_publisher = "Dotmac Technologies"
app_description = "AI-powered Business Intelligence Assistant that integrates directly with ERPNext as a custom DocType. This solution allows managers to query business data in natural language across both ERPNext and Splynx systems."
app_email = "info@dotmac.ng"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "bi_assisstant",
# 		"logo": "/assets/bi_assisstant/logo.png",
# 		"title": "Business Intelligence Assistant",
# 		"route": "/bi_assisstant",
# 		"has_permission": "bi_assisstant.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/bi_assisstant/css/bi_assisstant.css"
# app_include_js = "/assets/bi_assisstant/js/bi_assisstant.js"

#app_include_css = "/assets/bi_assistant/css/bi-assistant-css.css"
#app_include_js = "/assets/bi_assistant/js/bi-assistant.js"

# include js, css files in header of web template
# web_include_css = "/assets/bi_assisstant/css/bi_assisstant.css"
# web_include_js = "/assets/bi_assisstant/js/bi_assisstant.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "bi_assisstant/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "bi_assisstant/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "bi_assisstant.utils.jinja_methods",
# 	"filters": "bi_assisstant.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "bi_assisstant.install.before_install"
# after_install = "bi_assisstant.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "bi_assisstant.uninstall.before_uninstall"
# after_uninstall = "bi_assisstant.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "bi_assisstant.utils.before_app_install"
# after_app_install = "bi_assisstant.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "bi_assisstant.utils.before_app_uninstall"
# after_app_uninstall = "bi_assisstant.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "bi_assisstant.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"bi_assisstant.tasks.all"
# 	],
# 	"daily": [
# 		"bi_assisstant.tasks.daily"
# 	],
# 	"hourly": [
# 		"bi_assisstant.tasks.hourly"
# 	],
# 	"weekly": [
# 		"bi_assisstant.tasks.weekly"
# 	],
# 	"monthly": [
# 		"bi_assisstant.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "bi_assisstant.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "bi_assisstant.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "bi_assisstant.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["bi_assisstant.utils.before_request"]
# after_request = ["bi_assisstant.utils.after_request"]

# Job Events
# ----------
# before_job = ["bi_assisstant.utils.before_job"]
# after_job = ["bi_assisstant.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"bi_assisstant.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

