package com.travel.exception;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.HashMap;
import java.util.Map;

/**
 * 全局异常处理类：捕获并处理所有异常。
 */
@RestControllerAdvice
public class GlobalExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /**
     * 拦截 @Valid 触发的参数校验失败（比如前端传了500元预算）
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidationExceptions(MethodArgumentNotValidException ex) {
        Map<String, Object> response = new HashMap<>();
        response.put("success", false);
        response.put("code", 400);

        // 获取所有字段的报错信息
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getAllErrors().forEach((error) -> {
            String fieldName = ((FieldError) error).getField();
            String errorMessage = error.getDefaultMessage();
            errors.put(fieldName, errorMessage);
        });

        // 使用 String.join 将所有错误信息用分号拼接起来
        String combinedMessage = String.join("；", errors.values());
        if (combinedMessage.isEmpty()) {
            combinedMessage = "请求参数格式不正确";
        }
        response.put("errorMessage", combinedMessage);
        response.put("errors", errors); // 依然保留结构化的 Map，方便前端更灵活地处理

        log.warn("接口参数校验失败: {}", errors);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
    }

    /**
     * 拦截我们自己抛出的业务逻辑异常（比如出发日和结束日是同一天）
     */
    @ExceptionHandler(TravelValidationException.class)
    public ResponseEntity<Map<String, Object>> handleBusinessExceptions(TravelValidationException ex) {
        Map<String, Object> response = new HashMap<>();
        response.put("success", false);
        response.put("code", 400);
        response.put("errorMessage", ex.getMessage());

        log.warn("业务规则校验失败: {}", ex.getMessage());
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
    }
}
