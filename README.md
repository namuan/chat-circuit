# Chat Circuit

![](docs/img.png)

**Multi-Branch Conversations**
Create and manage multiple conversation branches seamlessly.

**Contextual Forking**
Fork conversation branches with accurate context retention.

### Model Configuration

The LLM models available are loaded from `models.conf` in the current directory
See `models.conf.example`

The default model is the first one in that list

You can also run this command to generate the `models.conf` file

```shell
ollama list | tail -n +2 | awk '{print $1}' > models.conf
```

Note: If models.conf is not found, the application will use a default set of models.
