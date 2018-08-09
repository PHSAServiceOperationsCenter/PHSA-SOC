SELECT 
n.Caption AS SERVER,
n.IPaddress AS IPAddress,
a.Name AS APP,
c.ComponentName AS CMPNT, 
ce.AvgStatisticData AS STAT, 
ce.ErrorMessage AS MSG

FROM
Orion.APM.Component(nolock=true) c 
JOIN Orion.APM.CurrentComponentStatus(nolock=true) ccs ON c.ComponentID = ccs.ComponentID 
JOIN Orion.APM.ChartEvidence(nolock=true) ce ON ce.ComponentStatusID = ccs.ComponentStatusID
JOIN Orion.APM.Application(nolock=true) a ON c.ApplicationID = a.ApplicationID
JOIN Orion.Nodes(nolock=true) n ON a.NodeID = n.NodeID


WHERE a.Name LIKE '%SSL%'

