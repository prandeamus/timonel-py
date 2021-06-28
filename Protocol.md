# Timonel Protocol

## Summary
These are notes to assist implementation; they are not definitive.

Upcoming - in the 1.6 release, all two-byte addresses will become little-endian throughout
(see discussion in the main timonel project).

| Command  | T0 | T1       | T2       |    | R0 | R1                 | R2 | 
|----------|----|----------|----------|----|----|--------------------|----|
| NO_OP    | 00 |          |          |    | FF |                    |    |
| RESETMCU | 80 |          |          |    | 7F |                    |    |
| INITSOFT | 81 |          |          |    | 7E |                    |    |
| GETTMNLV | 82 |          |          |    | 7D | Data*12            |    |
| DELFLASH | 83 |          |          |    | 7C |                    |    |
| STPGADDR | 84 | Page MSB | Page LSB | CHK? | 7B |CHK(T1,T2) |
| WRITPAGE | 85 | Addr LSB | Addr MSB | Byte* | 7A | CHK(T1,T2,Byte*) | ???
| EXITTMNL | 86 | -        |          |    | 79 |
| READFLSH | 87 | Addr MSB | Addr LSB | Len | 78 | Byte* | CHK(T1,T2,Byte*) |
| READDEVS | 88 | -  |    |   | 76 | Flags (10 bytes) |
| WRITEEPR | 89 | Addr MSB | Addr LSB | Byte | 75 | CHK(T1, T2, Byte)
| READEEPR | 8A | Addr MSB | Addr LSB | - | 74 | Byte | CHK(T1, T2, Byte)| 

## Sequence diagrams

I'm using mermaid for sequence diagrams. These are not processed natively by GitHub, so if you see no pictures below, try installed a browser extension such as "Github + Mermaid".

### DeleteApplication()
Delete user application
```mermaid
sequenceDiagram
    participant L as Loader
    participant M as Mcu
    L->>+M: DELFLASH
    M-->>-L: ACKDELFL
    L->>L: Wait 750ms
    L->>+M: NO_OP
    M-->>-L: UNKNOWNC
    Note over L,M: Continue to BootloaderInit()
```
### BootloaderInit()
```mermaid
sequenceDiagram
    participant L as Loader
    participant M as Mcu
    L->>+M: GETMNLV
    M-->>-L: ACKTMNLV, 12 bytes
    Note right of M: Query Status
    opt Two Step Init
        L->>L: Short delay
        L->>+M: NO_OP
        M-->>-L: ACK
        L->>L: Short delay
        L->>+M: INITMICRO
        M-->>-L: ACK
    end
```
### QueryStatus()
```mermaid
sequenceDiagram
    participant L as Loader
    participant M as Mcu
    L->>+M: GETMNLV
    M-->>-L: ACKTMNLV, 12 bytes
```
### UploadApplication(payload[], payload_size, uint16_t start_address)
Upload payload to MCU running Timonel

If AUTO_PAGE_ADDR is enabled, bootloader calculates addresses
```mermaid
sequenceDiagram
    participant L as Loader
    participant M as Mcu
    opt payload_size <= bootloader_start-TRAMPOLINE_LEN
        Note Right of M: No action, fits
    end

    Note over L,M: Common
    loop for each packet
        Note right of L: Variable packet sizes
        L->>+M: SendDataPacket(packet)
        M-->>-L: ack
        L->>L: Delay DLY_PKT_SEND
        opt packet errors>0
            Note over L,M: DeleteApplication() and quit
        end
        opt page end detected && NOT AUTO_PAGE_ADDR
            L->>L: Delay DLY_FLASH_PG
            L->>+M: SetPageAddress(start address+next page)
            M-->>-L: ack
        end
        L->>L: Delay DLY_FLASH_PG
    end
```
If AUTO_PAGE_ADDR is disabled, loader calculates pages addresses.
Features must have F_AUTO_PAGE_ADDR
```mermaid
sequenceDiagram
    participant L as Loader
    participant M as Mcu
    opt startAddress >= SPM_PAGESIZE
        Note Right of M: Fix reset vector to jump to Timonel
        L->>+M: FillSpecialPage(RST_PAGE)
        M-->>-L: ack
        L->>+M: SetPageAddress(start_address)
        M-->>-L: ack
        L-->>L: Delay FLASH_FG
    end
    opt payload_size <= bootloader_start-TRAMPOLINE_LEN
        Note Right of M: Check app fits in memory
        L->>+M: FillSpecialPage(TPL_PAGE, payload[1], payload[0])
        M-->>-L: ack
        L->>+M: SetPageAddress(startAddress)
        M-->>-L: ack
        L-->>L: Delay FLASH_FG
    end
``` 
### RunApplication()
```mermaid
sequenceDiagram
    participant L as Loader
    participant M as Mcu
    L->>+M:EXITTMNL
    M-->>-L:ACKEXITT
    L->>+M: GETTMNLV
    Note Right of M: needed to force Timonel exit
    M-->>-L: ACKTMLNV
```

## To add:

Try/Retry count for each command
Delay after command (after failure or success?)
Why STPGADDR has different byte order?

# See also
| URL | Comments |
|-----|----------|
| https://github.com/casanovg/Nb_TimonelTwiM/ | Sample uploader code |
| https://github.com/casanovg/nb-twi-cmd/blob/master/extras/Nicebots-Pluggie-I2C-Commands.xlsx | Command summary |
| https://github.com/casanovg/timonel/discussions/28 | Discussion thread |