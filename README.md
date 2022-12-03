# ftc-livestream-switcher
This utility will connect to the FIRST Tech Challenge scoring software to receive the status of the competition, switch the active OBS scene to the appropriate field, and begin recording the match. Once the match is over, it will automatically end the recording. After the competition, the video files can be uploaded to YouTube relatively quickly when compared to manually splicing the livestream archive.

## FTC Scoring Software Documentation
http://localhost/swagger-docs/api.html

## Downloading
Navigate to the releases section and click on the zip file appropriate for your system. If your operating system is not listed, download the source file.

## Usage
`usage: pyswitcher.exe [-h] -scoring scoringaddr -code eventcode -obs obsaddr [-port obsport] [-pw obspw]`  
`example: pyswitcher.exe -scoring "192.168.0.4" -code "01" -obs "localhost"`  
From a command prompt or terminal, run `pyswitcher.exe` with the supplied arguments. To find the scoring address, look at the top of the FTC scorekeeper page on the laptop running the scorekeeper software. Typically, the computer running pyswitcher and OBS will be the same, so simply passing `localhost` as the OBS address will suffice. If this is not the case, the OBS address can be found by opening a command prompt on the computer running OBS and typing the command `ipconfig`. The correct address is the `ipv4` entry under the adapter used to connect to the scoring network. Both the port and pw arguments are optional; the port will default to 4444 if nothing is specified. For a list of all parameters, run `pyswitcher.exe -h`  for help.
