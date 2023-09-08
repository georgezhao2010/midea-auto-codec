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

## 实体映射
映射文件位于`device_map/device_mapping.py`, 目前支持映射的实体类型如下:
- climate
- switch
- sensor
- binary_sensor

## 安装与配置
- 基于HomeAssistant Flow Config UI配置
- 在初次配置的时候，由于要安装三方Python库lupa，所以可能会转一会，正常现象，等着就行。
