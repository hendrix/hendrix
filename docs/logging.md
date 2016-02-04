
Here is a basic configuration of a logger that will output all logging which propagates to the hendrix server.

```
from twisted.logger import globalLogPublisher, LogLevel
from hendrix.logger import hendrixObserver

globalLogPublisher.addObserver(hendrixObserver(path='/my/log/path.txt', log_level=LogLevel.debug))
```


