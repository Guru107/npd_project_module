app_name = "npd_project_module"
app_title = "NPD Project Module"
app_publisher = "Guru107"
app_description = "Customization on top of existing Project Module in ERPNext to support NPD (New Product Development) process in a manufacturing company"
app_email = "connect@gurudatt.in"
app_license = "mit"

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "npd_project_module",
# 		"logo": "/assets/npd_project_module/logo.png",
# 		"title": "Npd Project Module",
# 		"route": "/npd_project_module",
# 		"has_permission": "npd_project_module.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/npd_project_module/css/npd_project_module.css"
# app_include_js = "/assets/npd_project_module/js/npd_project_module.js"

# include js, css files in header of web template
# web_include_css = "/assets/npd_project_module/css/npd_project_module.css"
# web_include_js = "/assets/npd_project_module/js/npd_project_module.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "npd_project_module/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Project": "public/js/project.js", "Task": "public/js/task.js"}
doctype_list_js = {"Task": "public/js/task_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "npd_project_module/public/icons.svg"

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

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "npd_project_module.utils.jinja_methods",
# 	"filters": "npd_project_module.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "npd_project_module.install.before_install"
after_install = "npd_project_module.install.after_install.after_install"

# Uninstallation
# ------------

before_uninstall = "npd_project_module.uninstall.before_uninstall.before_uninstall"
# after_uninstall = "npd_project_module.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "npd_project_module.utils.before_app_install"
# after_app_install = "npd_project_module.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "npd_project_module.utils.before_app_uninstall"
# after_app_uninstall = "npd_project_module.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "npd_project_module.notifications.get_notification_config"

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

# Document Events
# ---------------
# Note: Using client scripts and server scripts instead of doc_events hooks
# See public/js/project.js and public/js/task.js for client-side handlers
# See utils/project_utils.py and utils/task_utils.py for server-side methods

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"npd_project_module.tasks.all"
# 	],
# 	"daily": [
# 		"npd_project_module.tasks.daily"
# 	],
# 	"hourly": [
# 		"npd_project_module.tasks.hourly"
# 	],
# 	"weekly": [
# 		"npd_project_module.tasks.weekly"
# 	],
# 	"monthly": [
# 		"npd_project_module.tasks.monthly"
# 	],
# }

# Testing
# -------

before_tests = "npd_project_module.utils.test_setup.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "npd_project_module.custom.task.CustomTaskMixin"
# }

# Override DocType Class
# ------------------------------
#
# Override the standard doctype controller with custom implementation.
# Note: Using doc_events instead of override_doctype_class for Project
# override_doctype_class = {
# 	"Project": "npd_project_module.custom.doctype.project.project.Project"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "npd_project_module.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
	"Project": "npd_project_module.utils.dashboard_overrides.get_project_dashboard_data"
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["npd_project_module.utils.before_request"]
# after_request = ["npd_project_module.utils.after_request"]

# Job Events
# ----------
# before_job = ["npd_project_module.utils.before_job"]
# after_job = ["npd_project_module.utils.after_job"]

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
# 	"npd_project_module.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
