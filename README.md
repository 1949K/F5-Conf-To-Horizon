# 1、下载
右侧Releases中有两个文件，一个X86 windows，一个arm MacOS，下载相应的版本。

# 2、运行
双击运行。

# 3、使用
如果你有多个配置文件位于 /test 目录，例如
```
> tree -L 3
├── ucs1
│   ├── config
│   │   ├── bigip.conf
│   │   ├── bigip_base.conf
├── ucs1.zip
├── ucs2
│   ├── config
│   │   ├── bigip.conf
│   │   ├── bigip_base.conf
└── ucs2.zip
```

## 1-UCS后缀改为ZIP
此工具可以将你选择的文件夹中的所有ucs文件后缀改为zip，这对mac是很有用的，对于windows，你可能需要手动解压。

## 2-提取conf和base
此工具可以将选择的文件夹中的文件夹遍历，提取（选择的文件夹）中的（ucs文件夹）中的 （config文件夹）中的bigip.conf和 bigip_base.conf 到一级文件夹中，并分开存放。
此工具对于同时处理多个翻译时，非常有用。如果你只需要翻译一个ucs，可以仅仅使用 3-conf翻译为txt和excel 和 4-base翻译为txt和excel 。

例如，你选择了test目录，则可以生成如下内容。
```
> tree -L 2
├── bigip_base
│   ├── ucs1_bigip_base.conf
│   └── ucs2_bigip_base.conf
├── bigip_conf
│   ├── ucs1_bigip.conf
│   └── ucs2_bigip.conf
├── ucs1
├── ucs1.zip
├── ucs2
└── ucs2.zip
```

## 3-conf翻译为txt和excel
此工具可以将选择的文件夹中的所有 conf 文件翻译为 弘积的配置文件、配置汇总表和注意事项
此时，你应该选择 /test/bigip_conf 目录
```
> tree -L 2
├── bigip_base
│   ├── ucs1_bigip_base.conf
│   └── ucs2_bigip_base.conf
├── bigip_conf
│   ├── ucs1_bigip.conf
│   ├── ucs1_bigip.txt
│   ├── ucs1_bigip.xlsx
│   ├── ucs1_bigip_attention.txt
│   ├── ucs2_bigip.conf
│   ├── ucs2_bigip.txt
│   ├── ucs2_bigip.xlsx
│   └── ucs2_bigip_attention.txt
```

## 4-base翻译为txt和excel
此工具可以将选择的文件夹中的所有 conf 文件翻译为 弘积的配置文件、配置汇总表和注意事项
```
> tree -L 2
├── bigip_base
│   ├── ucs1_bigip_base.conf
│   ├── ucs2_bigip_base.conf
├── bigip_conf
│   ├── ucs1_bigip.conf
│   ├── ucs1_bigip.txt
│   ├── ucs1_bigip.xlsx
│   ├── ucs1_bigip_attention.txt
│   ├── ucs2_bigip.conf
│   ├── ucs2_bigip.txt
│   ├── ucs2_bigip.xlsx
│   └── ucs2_bigip_attention.txt
```


