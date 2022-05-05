"""
Methods
1. Register. POST
Register an app user Platform. This endpoint also logs the user in (returns the session token and roles), so you don't have to do another API call to log him in.
@:param str email: The user's email address
@:param str email: A hard to guess password
@:param str app: The appID given in the panel

2. Login. POST.
Login an app user at Platform.
Returns the session token and roles.
The object "roles" identifies the resources and things that the user has authorized the app to access.
@:param str email: The user's email address
@:param str email: A hard to guess password
@:param str app: The appID given in the panel

3. Link thing. POST
me/things
Before getting the user's data from a thing, a procedure called link thing is necessary, which allows the platform to know that the user is the owner of the thing.
@:param str thingToken: THING_TOKEN
@:param str Authorization: SESSION_TOKEN

4. Get resources. GET
me/resources
Get the user's resources and the things associated to each resource.
@:param str Authorization: SESSION_TOKEN

5. Get resource values
me/resources/{RESOURCE}
This endpoint returns the values of the specified resource.
@:param str RESOURCE:
@:param int limit: Max. number of values to be returned (Max.: 100)
@:param str startDate: The min date (format: YYYYMMDDHHmmss). The default is Jan 1st 1970.
@:param str endDate: The max date (format: YYYYMMDDHHmmss). The default is the end of times (javascript).
@:param str Authorization: SESSION_TOKEN

6. Get User Settings. GET
me/settings
Sometimes the app needs to store additional data about the user like name, company.
In that case the app can use the endpoint '/me/settings' in order to set and get the user’s settings.
The user’s settings are not meant to store large amounts of data. It’s more likely a small key/value store.
@:param str Authorization:SESSION_TOKEN

7. Update User Settings. PUT
me/settings
@:param json Settings: Settings JSON
@:param str Authorization:SESSION_TOKEN

8. Get Server Date. GET
utils/date/?format={FORMAT}
Retrieve the date of the server. The parameter format accepts two values: 'UTC' and 'unix_timestamp'.
@:param str FORMAT: Accepts two values: 'UTC' and 'unix_timestamp'.
@:param json: Settings JSON

TODO: Firmware Over-The-Air (OTA) update
TODO: Cloud Code Triggers

9. Available Thread Networks

10. Join Thread Networks

11.Form Thread Networks
@:param str Network Name:
@:param str PAN ID:
@:param str Network Ext PAN ID:
@:param str Network Key:
@:param str Channel
@:param str On-Mesh Prefix:
@:param bool Default Route:

12. Status

13. Settings
@:param str On-Mesh Prefix:
@:param bool Default Route:

14. Commission
@:param str Network Passphrase
@:param str Joiner PSKd
"""
