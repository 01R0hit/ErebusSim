import org.arl.fjage.RealTimePlatform

platform = RealTimePlatform

simulate {
  node 'Surface_Base', address: 1, api: 1101, web: 8081
  node 'scanner_1',    address: 2, api: 1102, web: 8082
  node 'scanner_2',    address: 3, api: 1103, web: 8083
}

