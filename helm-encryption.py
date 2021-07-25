#!/usr/bin/python3.9
import argparse, os, glob, yaml, sys, subprocess, shutil

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
script_dir = os.path.dirname(os.path.realpath(__file__))


group.add_argument("--encrypt",
                    "-e",
                    action='store_true',
                    help="encrypt the given chart values file")
group.add_argument("--decrypt",
                    "-d",
                    action='store_true',
                    help="decrypt the given chart values file")
group.add_argument("--clean",
                    "-c",
                    action='store_true',
                    help="clean all temporary files")
group.add_argument("--overwrite",
                    "-w",
                    action='store_true',
                    help="overwrite values file with encrypted values")
parser.add_argument("--key",
                    "-k",
                    type=str,
                    help="the base64 encoded aes key used to decrypt or encrypt the secret")
parser.add_argument("--path",
                    "-p",
                    type=str,
                    help="the path to the Helm chart directory")
parser.add_argument("--keyprefix",
                    "-x",
                    type=str,
                    default="encrypted",
                    help="the prefix of keys that should be encrypted (default - \"encrypted\")")
parser.add_argument("--values",
                    "-f",
                    type=str,
                    default="values.yaml",
                    help="the values file name (default - \"values.yaml\")")
parser.add_argument("--quiet",
                    "-q",
                    action='store_true',
                    help="quiet output mode")

args = parser.parse_args()

def cleanup_encrypt_files():
  if not args.quiet:
    print ("Cleaning up directory structure")
    print ("Deleting *.enc.yaml files")
  for f in glob.glob(os.path.join(args.path,"*.enc.yaml")):
    os.remove(f)

def cleanup_decrypt_files():
  if not args.quiet:
    print ("Cleaning up directory structure")
    print ("Deleting *.dec.yaml files")
  for f in glob.glob(os.path.join(args.path,"*.dec.yaml")):
    os.remove(f)

def encrypt_value(value):
  try:
      helm_response = subprocess.check_output(['helm', 'template', script_dir + '/encrypt', '--set', 'encrypt=' + value, '--set', 'aesKey=' + args.key], stderr=subprocess.DEVNULL)
      parsed_yaml = yaml.load(helm_response, Loader=yaml.FullLoader)
      for key, value in parsed_yaml["data"].items():
        if key == "encryptedSecret":
          return value
  except subprocess.CalledProcessError as helm_exception:
      return None

def decrypt_value(value):
  try:
      helm_response = subprocess.check_output(['helm', 'template', script_dir + '/encrypt', '--set', 'decrypt=' + value, '--set', 'aesKey=' + args.key], stderr=subprocess.DEVNULL)
      parsed_yaml = yaml.load(helm_response, Loader=yaml.FullLoader)
      for key, value in parsed_yaml["data"].items():
        if key == "decryptedSecret":
          return value
  except subprocess.CalledProcessError as helm_exception:
      return None

def perform_cipher_operation():
  if not os.path.isfile(os.path.join(args.path,"values.yaml")):
    print("Helm chart or values file not found in path {}. Exiting...".format(os.path.join(args.path,"values.yaml")))
    exit(1)

  encryptedFile = None
  decryptedFile = None
  if args.encrypt:
    cleanup_encrypt_files
    encryptedFile = open(os.path.join(args.path,"values.enc.yaml"), 'w')
  if args.decrypt:
    cleanup_decrypt_files
    decryptedFile = open(os.path.join(args.path,"values.dec.yaml"), 'w')


  valuesFile = os.path.join(args.path,args.values)
  with open(valuesFile) as vf:
    line = vf.readline()
    while line:
      parsed_yaml = yaml.load(line.strip(' -'), Loader=yaml.FullLoader)
      if parsed_yaml is not None:
        if hasattr(parsed_yaml, "items"):
          for key, value in parsed_yaml.items():
            if key.startswith(args.keyprefix):
              #Attempt to decrypt the value
              if decrypt_value(str(value).strip()) is not None:
                if args.encrypt:
                  encryptedFile.write(line)
                else:
                  decryptedFile.write(line.replace(str(value),decrypt_value(str(value).strip())))
              else:
                if args.encrypt:
                  encryptedFile.write(line.replace(str(value),encrypt_value(str(value).strip())))
                else:
                  decryptedFile.write(line)
            else:
              if args.encrypt:
                encryptedFile.write(line)
              else:
                decryptedFile.write(line)
      else:
        if args.encrypt:
          encryptedFile.write(line)
        else:
          decryptedFile.write(line)
      line = vf.readline()


if args.clean:
  if not args.path:
    print("--path value must be supplied")
    exit(1)
  cleanup_encrypt_files()
  cleanup_decrypt_files()

if args.encrypt or args.decrypt:
  if not args.path:
    print("--path value must be supplied")
    exit(1)
  if not args.key:
    print("--key value must be supplied")
    exit(1)
  perform_cipher_operation()

if args.overwrite == True:
  src = os.path.join(args.path,"values.enc.yaml")
  dst = os.path.join(args.path,args.values)
  if os.path.isfile(src):
    shutil.copy2(src, dst)
