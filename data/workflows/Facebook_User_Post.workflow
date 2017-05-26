<?xml version="1.0" ?>
<workflows>
	<workflow name="facebookUserPostWorkflow">
		<options>
			<enabled>true</enabled>
			<scheduler autorun="false" type="cron">
				<sDT>2016-1-1 12:00:00</sDT>
				<interval>0.1</interval>
				<eDT>2016-3-15 12:00:00</eDT>
			</scheduler>
		</options>
		<start>2</start>
		<steps>
			<step id="2">
				<id>2</id>
				<app>FacebookUserPost</app>
				<action>post_to_user_wall</action>
				<device/>
				<position>
					<x>425</x>
					<y>282</y>
				</position>
				<input>
					<message format="str">Explore WALKOFF at https://github.com/iadgov/WALKOFF :D :D :D</message>
				</input>
			</step>
			<step id="1">
				<id>1</id>
				<app>FacebookUserPost</app>
				<action>add_facebook_user</action>
				<device/>
				<position>
					<x>253</x>
					<y>159</y>
				</position>
				<input>
					<user_access_token format="str">Get from Facebook Developer Account</user_access_token>
					<user_id format="str">Get from Facebook Developer Account</user_id>
				</input>
				<next step="2"/>
			</step>
		</steps>
	</workflow>
</workflows>
