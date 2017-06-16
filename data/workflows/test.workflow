<?xml version="1.0" ?>
<workflows>
	<workflow name="test2">
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
			<step id="1">
				<name>1</name>
				<app>ARDrone</app>
				<action>move_backward</action>
				<position>
					<x>490</x>
					<y>430</y>
				</position>
				<inputs>
					<millisec>1000</millisec>
					<speed>1</speed>
				</inputs>
				<next step="2"/>
			</step>
			<step id="3">
				<name>3</name>
				<app>ARDrone</app>
				<action>move_forward</action>
				<position>
					<x>690</x>
					<y>390</y>
				</position>
				<inputs>
					<millisec>3000</millisec>
					<speed>3</speed>
				</inputs>
			</step>
			<step id="2">
				<name>2</name>
				<app>ARDrone</app>
				<action>move_down</action>
				<position>
					<x>570</x>
					<y>390</y>
				</position>
				<inputs>
					<millisec>5000</millisec>
					<speed>5</speed>
				</inputs>
				<next step="3"/>
			</step>
		</steps>
	</workflow>
</workflows>
