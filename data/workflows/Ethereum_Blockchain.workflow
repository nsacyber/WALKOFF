<?xml version="1.0" ?>
<workflows>
	<workflow name="ethereumBlockchainWorkflow">
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
			<step id="start">
				<id>start</id>
				<app>EthereumBlockchain</app>
				<action>create_accounts</action>
				<position>
					<x>173</x>
					<y>133</y>
				</position>
				<input>
					<total_nodes format="int">5</total_nodes>
				</input>
				<next step="2"/>
			</step>
			<step id="3">
				<id>3</id>
				<app>EthereumBlockchain</app>
				<action>submit_greeting</action>
				<position>
					<x>348.096805232115</x>
					<y>338.1871205254445</y>
				</position>
				<input>
					<greeting format="str">Hello human user!!</greeting>
				</input>
			</step>
			<step id="2">
				<id>2</id>
				<app>EthereumBlockchain</app>
				<action>set_up_network</action>
				<position>
					<x>236.6709793476604</x>
					<y>232.47543955814143</y>
				</position>
				<input/>
				<next step="3"/>
			</step>
		</steps>
	</workflow>
</workflows>
