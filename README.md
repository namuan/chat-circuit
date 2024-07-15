# Chat Circuit

![](docs/img.png)

### Features

**Multi-Branch Conversations**
Create and manage multiple conversation branches seamlessly.

**Contextual Forking**
Fork conversation branches with accurate context retention.

### Running the Application

To run this application, follow these steps:

**Generate models configuration file**

```shell
ollama list | tail -n +2 | awk '{print $1}' > models.conf
```

**Install dependencies**

```shell
python3 -m pip install -r requirements.txt
```

**Run application**
```shell
python3 main.py
```

### Model Configuration

The LLM models available are loaded from `models.conf` in the current directory
See `models.conf.example`

The default model is the first one in that list

You can also run this command to generate the `models.conf` file

```shell
ollama list | tail -n +2 | awk '{print $1}' > models.conf
```

Note: If models.conf is not found, the application will use a default set of models.
