# Подготовка к решению тестового задания:
Написание простого веб-приложения [app.py](https://github.com/tkhrustaleva/Interview-task/blob/feature/init/app.py), с помощью которого можно будет проверить работоспособность предлагаемого решения;

Публикация образа приложения в репозиторий DockerHub:

* составление файлов [Dockerfile](https://github.com/tkhrustaleva/Interview-task/blob/feature/init/Dockerfile) и [requirements](https://github.com/tkhrustaleva/Interview-task/blob/feature/init/requirements.txt)

* добавление приложения в [DockerHub](https://github.com/tkhrustaleva/Interview-task) 
```
docker build -t flackapp:v0.2 . 
docker run -it flackapp:v0.2
docker tag flackapp:v0.1 tatita/flackapp:v0.2
docker push tatita/flackapp:v0.2
```

# Настройка тестового окружения
* Запускаем minikube и увеличиваем количество Нод до трех (трех Нод будет достаточно для тестирования решения):
```
minikube start
minikube node add
minikube node add
```
![](/assets/getnodes.jpg ':size=50%')
* Вешаем на Ноды необходимые лэйблы:
```
kubectl label nodes minikube app=flaskapp
kubectl label nodes minikube zone=zone1
kubectl label nodes minikube-m02 app=flask
kubectl label nodes minikube-m02 zone=zone2
kubectl label nodes minikube-m03 app=flask
kubectl label nodes minikube-m03 zone=zone3
```
![](/assets/showlabels.jpg ':size=75%')
* Включаем работу метрик:
```
minikube addons enable metrics-server
```

# Решение тестового задания
Cоставление [deployment.yaml](https://github.com/tkhrustaleva/Interview-task/blob/feature/init/deployment.yaml), согласно вводным данным.
Поясню свои решения, процитировав полученные требования:

* `replicas: 2` выбрано как минимально надежное количество реплик. Таким образом, мы покрываем требование рациональности использования ресурсов (в случае низкой нагрузки у нас не будут избыточно расходоваться ресурсы). Однакоо мы сталкиваемся с проблемой доступности и отказоустойчивости приложения. Данная проблема будет решена ниже.

* Использование ресурсов контролирует `resources`, а именно:

    `requests` дает гарантированное количество ресурсов - наше приложение не будет ущемлено, что позволит функционировать нормально; 

    `limits` ограничивает потребляемые ресурсы. Если приложение начинает использовать слишком много ресурсов, создает их дефицит, ограничивает другие Поды, то K8s ограничит потребление его ресурсов в указанных пределах.

* Использование Проб

    Проблему долгого запуска решаем с помощью `startupProbe`, которая блокирует проверку `livenessProbe` и `readinessProbe`. Приложение стартует минимум 5 секунд, поэтому именно через такой промежуток времени впервые произойдет наша Проба. В случае неуспеха через 5 секунд Проба снова сработает, к этому времени пройдет 10 секунд - максимальное время старта приложения. Таким образом, `failureThreshold * periodSeconds` достаточно, чтобы покрыть наихудшее время старта. Если Проба снова прошла неуспешно, то приложение будет рестартовано.

    Если веб-приложение запустилось, работало, а потом зависло и совсем не отвечает, оно будет рестартовано по причине непрохождения `livenessProbe`.

    Если на Под был направлен запрос, который он обрабатывает длительное количество времени, то с помощью `readinessProbe` трафик будет перенаправляться на другие Поды.

* Добавление `topologySpreadConstraints`

    Kubernetes автоматически распределяет Поды по различным Нодам Кластера, снижая влияние падений Нод. Однако мы можем использовать Лэйблы на Нодах для обозначения Зон совместно с [Pod topology spread constraints](https://kubernetes.io/docs/concepts/workloads/pods/pod-topology-spread-constraints/) в целях контролирования того, как Поды распределяются по Кластеру. 

    ![Ноды](/assets/nodes-02.jpg)

    Если бы мы не использовали `topologySpreadConstraints`, то для защиты от падения целой Зоны мы бы выставляли минимальное количество реплик Подов равное 3. Использование данного функционала позволяет нам поставить минимальное количество реплик равное 2. Так мы сохраняем максимальную доступность при минимуме используемых ресурсов.

# Дополнительное решение задания

* Cоставление [hpa.yaml](https://github.com/tkhrustaleva/Interview-task/blob/feature/init/hpa.yaml) - [HorizontalPodAutoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) - автоматический скэйлинг загруженности

Изначально поднимается минимально необходимое количество реплик равное 2. В случае максимальной нагрузки (возрастания CPU) - днем - количество реплик возрастет до максимума равного 4. А когда нагрузка спадает (падения CPU) - ночью - HPA уменьшит количество реплик снова до минимального - до 2.

Проверить нагрузку на Ноды можно с помощью команды:
```
kubectl top pods -n mindbox
kubectl get pods.metrics.k8s.io -n mindbox
```

![Ноды](/assets/metrics.jpg ':size=55%') 

* Составление [pdb.yaml](https://github.com/tkhrustaleva/Interview-task/blob/feature/init/pdb.yaml) - [PodDisruptionBudget](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) для блокировки удаления Ноды с работающей репликой веб-приложения

Видим, на каких Нодах работают Поды

![trt](/assets/podonnode.jpg ':size=75%')

После применения манифеста работоспособность можно проверить путем выполнения следующих команд:
```
kubectl get poddisruptionbudgets -n mindbox
kubectl drain minikube-m02 --ignore-daemonsets
```

Удаление невозможно

![tg](/assets/del.jpg ':size=70%')

Для возрата Ноды в исходное состояние (Status = Ready) выполним команду:
```
kubectl uncordon minikube-m02
```

# Helm-chart 

Составление [helm-chart для веб-приложения](https://github.com/tkhrustaleva/Interview-task/tree/feature/init/flask-chart) - инструмента шаблонизации манифестов

```
helm create flask-chart
helm install test flask-chart --dry-run
helm install flaskapp flask-chart -n mindbox
```

Проверка деплоя:
```
k get hpa -n mindbox
k delete hpa flaskapp-hpa -n mindbox 
k get hpa -n mindbox
helm list -n mindbox
helm rollback -n mindbox flaskapp 1
k get hpa -n mindbox
helm upgrade --install flaskapp flask-chart -n mindbox
```

# Публикация решения в GitHub, составление документации

```
git init
git remote add origin https://github.com/tkhrustaleva/Interview-task.git
git checkout -b feature/init
git add .
git commit -m 'first commit'
git push origin feature/init
```