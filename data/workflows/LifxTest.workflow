<?xml version="1.0" ?>
<workflows>
	<workflow name="Test">
		<options>
			<enabled>true</enabled>
			<scheduler autorun="false" type="cron">
				<sDT>2016-1-1 12:00:00</sDT>
				<interval>0.1</interval>
				<eDT>2016-3-15 12:00:00</eDT>
			</scheduler>
		</options>
		<start>1</start>
		<steps>
			<step id="1">
				<name>1</name>
				<app>Lifx</app>
				<action>breathe</action>
				<device>LIFX 12cf1f</device>
				<position>
					<x>494.055032258</x>
					<y>437.567112283</y>
				</position>
				<inputs>
					<power_on>True</power_on>
					<color>red</color>
					<period>1.0</period>
					<peak>0.5</peak>
					<persist>False</persist>
					<from_color>blue</from_color>
					<cycles>5.0</cycles>
				</inputs>
				<next step="2"/>
			</step>
			<step id="3">
				<name>3</name>
				<app>Lifx</app>
				<action>pulse</action>
				<device>LIFX 12cf1f</device>
				<position>
					<x>406.540089357</x>
					<y>333.60458204</y>
				</position>
				<inputs>
					<power_on>True</power_on>
					<color>red</color>
					<period>1.0</period>
					<persist>True</persist>
					<from_color>blue</from_color>
					<cycles>10.0</cycles>
				</inputs>
			</step>
			<step id="2">
				<name>2</name>
				<app>Lifx</app>
				<action>toggle power</action>
				<device>LIFX 12cf1f</device>
				<position>
					<x>452.952347395</x>
					<y>381.806710298</y>
				</position>
				<inputs>
					<duration>2.0</duration>
				</inputs>
				<next step="3"/>
			</step>
		</steps>
	</workflow>
</workflows>
