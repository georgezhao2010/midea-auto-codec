# Midea Meiju Codec
 
 [![Stable](https://img.shields.io/github/v/release/georgezhao2010/midea-meiju-codec)](https://github.com/georgezhao2010/midea-meiju-codec/releases/latest)

通过网络获取你美居家庭中的设备，并且在本地配置这些设备，并通过本地更新状态及控制设备。

- 自动查找和发现设备
- 自动下载设备的协议文件
- 将设备状态更新为设备可见的属性
- 仅在配置设备时联网一次，配置完成后纯本地工作

## 非常初期的预览版
- 仅供技术实现验证以及评估
- 所有设备默认可生成一个名为Status的二进制传感器，其属性中列出了设备可访问的所有属性，当然有些值不可设置
- Status实体前几项列出了该设备的分类信息，供参考

## 实体映射
映射文件位于`device_mapping`下, 每个大的品类一个映射文件，目前支持映射的实体类型如下:
- sensor
- binary_sensor
- switch
- select
- climate
- fan
- water_heater

示例配置`22012227`演示了如何将设备属性映射成以上各种HomeAssistant中的实体。


## 安装与配置
- 基于HomeAssistant Flow Config UI配置
- 在初次配置的时候，由于要安装三方Python库lupa，所以可能会转一会，正常现象，等着就行。
