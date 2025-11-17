DELIMITER //

CREATE FUNCTION CalculateAgentCommission (
    sale_amount DECIMAL(10, 2)
)
RETURNS DECIMAL(10, 2)
DETERMINISTIC
BEGIN
    DECLARE commission_rate DECIMAL(3, 2) DEFAULT 0.025; -- 2.5% commission rate
    DECLARE commission DECIMAL(10, 2);

    SET commission = sale_amount * commission_rate;

    RETURN commission;
END //

DELIMITER ;

DELIMITER //

CREATE FUNCTION GetAverageGlobalRating (
    -- This function accepts NO parameters.
)
RETURNS DECIMAL(3, 2)
READS SQL DATA
BEGIN
    DECLARE avg_rating DECIMAL(3, 2);
    -- Calculates the average rating across all entries in the reviews table.
    SELECT AVG(rating) INTO avg_rating
    FROM reviews;

    -- If no reviews exist, return 0.00 instead of NULL.
    RETURN COALESCE(avg_rating, 0.00);
END //

DELIMITER ;

DELIMITER //

CREATE PROCEDURE MarkPastAppointmentsCompleted ()
BEGIN
    -- This UPDATE now correctly compares the 'datetime' column against NOW()
    UPDATE appointments
    SET 
        status = 'Completed'
    WHERE 
        -- Check if the single 'datetime' column is earlier than the current moment
        datetime < NOW()
        -- Only update appointments that are currently active
        AND status IN ('Pending', 'Confirmed');
        
END //

DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_BeforePropertyUpdate_CheckPriceDrop
BEFORE UPDATE ON properties
FOR EACH ROW
BEGIN
    -- DECLARE statement must come first
    DECLARE max_allowed_drop_price DECIMAL(15, 2);

    -- Only check if the price is changing and decreasing
    IF NEW.price IS NOT NULL AND OLD.price IS NOT NULL AND NEW.price < OLD.price THEN

        SET max_allowed_drop_price = OLD.price * 0.90; -- 90% of old price

        IF NEW.price < max_allowed_drop_price THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Price reduction exceeds the maximum allowed 10% limit.';
        END IF;
    END IF;
END //

DELIMITER ;
