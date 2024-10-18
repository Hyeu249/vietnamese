# quan-ly-tau-thuy-vsico

## development on local
Use `make` command.
```bash
$ make dev-local-start
```

To clean up the dev:
```bash
$ make dev-local-stop
```

## use dockerfile

1. docker build -t image-name .
2. setup postgres database
3. docker run -p 8069:8069 -v /path/to/your/config:/etc/odoo/ image-name
