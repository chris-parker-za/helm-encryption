# helm-encryption

*__Calling on contributors with Python skills to help take this project further__*

## Overview
This project aims to address some limitations of packaged charts in the [helm-secrets](https://github.com/jkroepke/helm-secrets) plugin in a helm-native way. This project does not aim to replace helm-secrets, in fact, helm-secrets is a perfectly good fit for most projects. helm-encryption works by targeting keys within an existing values file and encryption them using AES encryption. Importantly, the keys are encrypted with Helm itself, thereby not requiring this utility to decrypt the secrets within. That was the aim with this tool; i.e. to remove the dependence on external tools and plugins to decrypt secrets in Helm charts when doing an install or upgrade. 

## Rationale

When attempting to use helm-secrets for my project, my team ran into a few fundamental issues with the plugin:

1. Helm secrets operates on the entire values file. Secrets are extracted into their own values file and that file is then encrypted. This in principle works just fine, however, for a large values file, moving certain keys out into a separate file suffers an inherent maintainability loss. For example, if you have a large nested yaml structure with one or two secrets, moving these into their own file will either repeat that structure (sans all the other keys) or simply move the keys to be encrypted into a long list. This maintainability hit was not an option for my project.
2. Hem secrets requires a wrapper to the Helm tool. While in principle this is fine, this does always require the presence of the helm-secrets plugin 
3. Because of point 1 above, helm-secrets requires at least 2 values files. Again, in principle (for most projects) this is fine. However, if you are packaging your charts and shipping them off to a container registry or chart museum, you will run into issues when trying to install these charts. Helm (and by proxy, helm-secrets) does not support multiple values files inside a packaged chart. This therefore requires you to unpack the packaged chart first and then specify the values file you want to decrypt. 
4. Lastly, helm-secrets requires an external decryption routine to decrypt secrets - thus, editing secrets first requires you to decrypt the full list of secrets, then edit the secret and then re-encrypt the secret. This seemed unnecessary for our project.

## Requirements
- Helm 3.0 or higher
- Python 3.8 or higher

## Usage

This utility makes some assumptions:
1. The default values file `values.yaml` is always encrypted, i.e. your Helm chart has only 1 values file. You can change this behaviour by using the `--values` parameter
2. Keys prefixed with `encrypted` will be encrypted (or decrypted). You can change this behaviour by specifying an alternative prefix of your choice by using the `--keyprefix` parameter.
3. There is an assumption that *.dec.yaml and *.enc.yaml are added to `.gitignore` to prevent accidental checkin.

### Encrypt

Encrypt an existing value.yaml file. Encrypted all keys starting with the word `encrypted` unless an alternative prefix is specified.
The encryption key, by default, must be base64 encoded.

`./helm-encyption.py --encrypt --path <path to helm chart> --key <aesKey>`

**Example:**

```
databaseCredentials:
  encyptedUsername: mysql 
  encryptedPassword: superSecret123@
 ```
   

`/helm-encyption.py --encrypt --path /repo/my-helm-chart --key QiZFKUhATWNRZlRqV25acjR1N3gheiVDKkYtSmFOZFI=`

Decrypted values files will be saved as `values.yaml.enc` at the path specified with `--path`

_**NOTE:** This tool will not re-encrypt previously encrypted values provided the same (correct) key is used. It is therefore possible to append a new key to be encrypted without decrypting the file first_

### Decrypt

Decrypt an existing value.yaml file. Encrypted keys starting with the word `encrypted` will be decrypted unless an alternative prefix is specified. The decryption key, by default, must be base64 encoded.

`./helm-encyption.py --decrypt --path <path to helm chart> --key <aesKey>`

Decrypted values files will be saved as `values.yaml.dec` at the path specified with `--path`

**Example:**

`/helm-encyption.py --decrypt --path /repo/my-helm-chart --key QiZFKUhATWNRZlRqV25acjR1N3gheiVDKkYtSmFOZFI=`

### Overwrite

The encryption operation generates a new file called `values.enc.yaml`. This is done so that the file can be reviewed. The existing values file may be replaced with the newly encrypted file manually or by using this overwrite command.

`/helm-encyption.py --overwrite --path <path to helm chart>`

#### Clean

A convenience function for removing all `.dec.yaml` and `.enc.yaml` files from the specified path.

`/helm-encyption.py --clean --path <path to helm chart>`

## Usage in your Helm chart

Once you have an encrypted values file, the recommended way to pass the decryption key into your chart is using a `--set` statement.

Example:

`helm upgrade my-chart/ --set aesKey=QiZFKUhATWNRZlRqV25acjR1N3gheiVDKkYtSmFOZFI=`

In your template files, the value can be decrypted as follows:

`superSecret: {{ .Values.databaseCredentials.encryptedPassword | decryptAES (.Values.aesKey | b64dec)}}`


## Project Components

- `helm-encryption.py` - the main entrypoint 
- `/encrypt` - a simple Helm 3.0 chart that performs the encryption and decryption.

## Copyright and license
© 2020-2021 Christopher Parker (chris.parker.za)

Licensed under the [Apache License, Version 2.0](https://commons.apache.org/proper/commons-bsf/license.html)