.method public parse(Lcom/fasterxml/jackson/core/g;)Lcom/twitter/model/json/timeline/urt/JsonTimelineEntry;

	.locals 2

	.annotation system Ldalvik/annotation/Throws;

		value = {

			Ljava/io/IOException;

		}

	.end annotation



	.line 2

	invoke-static {p1}, Lcom/twitter/model/json/timeline/urt/JsonTimelineEntry$$JsonObjectMapper;->_parse(Lcom/fasterxml/jackson/core/g;)Lcom/twitter/model/json/timeline/urt/JsonTimelineEntry;



	move-result-object p1



	iget-object v0, p1, Lcom/twitter/model/json/timeline/urt/JsonTimelineEntry;->a:Ljava/lang/String;



	const-string v1, "KZK"

	invoke-static {v1, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I



	const-string v1, "promoted"

	invoke-virtual {v0, v1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z



	move-result v0



	if-eqz v0, :cond_b



	const/4 p1, 0x0



	:cond_b



	return-object p1

.end method