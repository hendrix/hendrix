
To configure global logging in any way you might desire, here is some example code to get you started. 

```
from twisted.logger import globalLogPublisher, LogLevel
from hendrix.logger import hendrixObserver

globalLogPublisher.addObserver(hendrixObserver(log_level=LogLevel.debug))
```


