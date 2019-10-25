Orion REST API
==============

The `Orion REST API` is provided by the
`SWIS - The SolarWinds Information Service
<https://github.com/solarwinds/OrionSDK/wiki/About-SWIS>`__.

The schemas for all the entities exposed via `SWIS
<https://github.com/solarwinds/OrionSDK/wiki/About-SWIS>`__ are available at
`SolarWinds Information Service v3.0 Schema Documentation Index
<https://solarwinds.github.io/OrionSDK/schema/index.html>`__.

The `Orion SDK` is available on `GitHub
<https://github.com/solarwinds/OrionSDK>`__. The most important component,
as far as we are concerned, is the `SWQL Studio` client. It allows one to
explore the `SWIS schemas
<https://solarwinds.github.io/OrionSDK/schema/index.html>`__ and the data
stored on the `Orion` server. Use this client to reverse-engineer 
`SWQL queries
<https://support.solarwinds.com/SuccessCenter/s/article/Use-SolarWinds-Query-Language-SWQL>`__
as needed by various :ref:`SOC Automation Server Applications`.

The :ref:`SOC Automation Project` and, in particular, the :ref:`Orion
Integration Application` are using the `Orion SDK for Python
<https://github.com/solarwinds/orionsdk-python>`__. Besides the code in the
:mod:`orion_integration.orion`, there are several interesting samples and
examples using the `Orion SDK for Python
<https://github.com/solarwinds/orionsdk-python>`__ under the undocumented and
inactive `orion_flash` application in the `orion_flash.orion` package.

:Note:

    It is very important to consult the code in the `Orion SDK for Python
    <https://github.com/solarwinds/orionsdk-python>`__ package after
    installation. The package is not well maintained and, sometimes, the
    documentation is not synchronized with the code.